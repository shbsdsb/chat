# Chat MVP 设计文档

> 日期：2026-07-19 · 分支：`develop` · 方案：纯 Vue 3 + Pinia + 手写 CSS

---

## 1. 概述

**产品定位**：AI 对话客户端（类 ChatGPT），MVP 阶段仅 Web 端。

**MVP 范围**：
- **API 设置页** — 预设管理（下拉选择/新建/删除/保存）、API URL/Key 配置、Model 下拉 + 拉取按钮、response_format 大文本输入
- **对话页** — 对话列表侧边栏、消息气泡流（用户右/AI左，白底黑字浅灰边框）、SSE 流式传输、发送/暂停按钮
- **AI 消息操作** — 编辑气泡、重放（重新生成）、版本左右切换

**MVP 明确不做**：
- 暗色主题、移动端适配
- Electron 桌面打包
- Markdown 渲染（纯文本）

**UI 风格**：类 ChatGPT 简约亮色主题 — 主色 `#fff`，辅助色白偏灰（`#f5f5f5` / `#fafafa`），灰色线边框（`#e0e0e0` / `#d5d5d5` / `#e8e8e8`），按钮统一浅灰色。

---

## 2. 路由

| 路径 | 视图 | 说明 |
|------|------|------|
| `/` | ChatView | 对话页（默认首页） |
| `/settings` | SettingsView | API 设置页 |

---

## 3. 组件树

```
App.vue
├── Sidebar.vue                  # 左侧对话列表栏（260px，始终可见）
│   ├── NewChatButton            # 顶部「新建对话」
│   └── ConversationItem.vue     # 单个对话项（选中高亮、右键删除/重命名）
│
├── (router-view)
│   ├── ChatView.vue             # 对话主页
│   │   ├── WelcomeBanner.vue    # 无对话时的引导欢迎语
│   │   ├── MessageList.vue      # 消息滚动区域
│   │   │   ├── MessageBubble.vue# 单条气泡（user 右 / assistant 左）
│   │   │   └── MessageActions.vue # 编辑·重放·←→切换（仅 AI 最后一条）
│   │   └── InputBar.vue         # 底部输入栏（含发送/暂停按钮）
│   │
│   └── SettingsView.vue         # 设置页
│       ├── PresetSelector.vue   # 预设下拉 + 新建/删除/保存
│       ├── ModelSelector.vue    # Model 下拉 + 拉取按钮
│       └── ResponseFormatInput.vue # response_format 大文本输入
```

---

## 4. Pinia Store

### 4.1 useSettingsStore

```js
state: {
  presets:          [],          // 预设列表
  activePresetId:   null,        // 当前选中预设 ID
  apiUrl:           '',          // 当前 API URL
  apiKey:           '',          // 当前 API Key
  model:            '',          // 当前 model
  responseFormat:   '',          // 当前 response_format
  availableModels:  [],          // 拉取到的 model 列表
}

actions: {
  loadPresets(),                // GET /api/settings
  selectPreset(id),             // 切换预设
  createPreset(name),           // POST /api/settings
  savePreset(),                 // PUT /api/settings/:id
  deletePreset(id),             // DELETE /api/settings/:id
  fetchModels(),                // GET /api/settings/models
}
```

### 4.2 useChatStore

```js
state: {
  conversations:    [],          // 对话列表
  activeConvId:     null,        // 当前对话 ID
  messages:         [],          // 当前对话消息
  isStreaming:      false,       // SSE 流状态
  abortController:  null,        // SSE 取消控制器
  aiVersionIndex:   0,           // 当前 AI 输出版本索引
  aiVersions:       {},          // { messageId: [v1, v2, ...] }
}

actions: {
  loadConversations(),           // GET /api/conversations
  createConversation(),          // POST /api/conversations
  deleteConversation(id),        // DELETE /api/conversations/:id
  renameConversation(id, title), // PUT /api/conversations/:id
  selectConversation(id),        // 切换对话 + 加载消息
  sendMessage(content),          // POST → SSE 流
  stopStreaming(),               // POST /api/conversations/:id/stop
  editMessage(id, content),      // PUT /api/messages/:id
  replayMessage(id),             // POST → SSE 新版本
  switchVersion(id, dir),        // ← → 切换版本
}
```

---

## 5. 页面布局

### 整体布局
```
┌──────────┬───────────────────────────────┐
│  Sidebar │      <router-view>            │
│  260px   │        flex: 1                │
│ #f5f5f5  │        #ffffff                │
└──────────┴───────────────────────────────┘
```

### 气泡样式
- 通用：白底黑字，圆角 12px，边框 `1px solid #e0e0e0`，padding 12px 16px，max-width 70%
- 用户气泡：`margin-left: auto`，边框 `#d5d5d5`
- AI 气泡：`margin-right: auto`，边框 `#e8e8e8`

### 输入栏
- 圆角 24px，边框 `1px solid #d5d5d5`，min-height 44px
- 发送按钮 ▶ 内置右侧，流式时变为 ⏸（暂停）

### 设置页
- 预设栏：下拉 + 新建 + 删除 + 保存，水平排列
- Model 栏：下拉 + 🔄 拉取按钮
- response_format：textarea，~150px 高，等宽字体

---

## 6. SSE 流式交互

```
前端                           后端
 ├── POST /chat ───────────────→ 保存 user msg，开始 SSE
 │←── data: {"delta":"你"} ────┤
 │←── data: {"delta":"好"} ────┤
 │←── data: {"done":true} ─────┤ 保存 assistant msg
 │                              │
 ├── POST /stop ───────────────→ 设置 cancel 标志
 │←── data: {"stopped":true} ──┤ SSE 关闭
 │                              │
 ├── POST /regenerate ─────────→ 删最后 assistant，重新 SSE
 │←── (新 SSE stream) ─────────┤ 新版本存入 aiVersions
```

---

## 7. 相关文档

| 文档 | 路径 |
|------|------|
| 前端设计（详细） | `docs/frontend/2026-07-19_chat-mvp-design.md` |
| 后端 API 设计 | `docs/api/2026-07-19_chat-api-design.md` |
| API 接口参考 | `docs/API.md` |
| 数据存储方案 | `docs/STORAGE.md` |
