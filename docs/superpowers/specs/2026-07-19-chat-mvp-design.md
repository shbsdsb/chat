# Chat 前端 MVP 设计文档

> 日期：2026-07-19 · 分支：`develop` · 方案：纯 Vue 3 + Pinia + 手写 CSS

---

## 1. 概述

**产品定位**：AI 对话客户端（类 ChatGPT），MVP 阶段仅 Web 端。

**MVP 范围**：
- **API 设置页** — 预设管理、API URL/Key 配置、Model 下拉 + 拉取、response_format
- **对话页** — 对话列表侧边栏、消息气泡流、SSE 流式、AI 回复操作按钮

**UI 风格**：类 ChatGPT 简约亮色主题 — 主色 `#fff`，辅助色白偏灰（`#f5f5f5` / `#e8e8e8`），灰色线边框（`#d5d5d5`），按钮统一浅灰色。

---

## 2. 路由

| 路径 | 视图 | 说明 |
|------|------|------|
| `/` | `ChatView` | 对话页（默认首页） |
| `/settings` | `SettingsView` | API 设置页 |

---

## 3. 组件树

```
App.vue
├── Sidebar.vue                  # 左侧对话列表栏（260px，始终可见）
│   ├── [新建对话] 按钮
│   └── ConversationItem.vue × N # 对话项（选中高亮、右键删除/重命名）
│
└── <router-view>
    ├── ChatView.vue             # / 对话主页
    │   ├── WelcomeBanner.vue    # 无对话时的引导欢迎语
    │   ├── MessageList.vue      # 消息滚动区域
    │   │   ├── MessageBubble.vue# 单条气泡（user 右 / assistant 左）
    │   │   └── MessageActions.vue # [编辑][重放][◀ ▶]（仅 AI 最后一条）
    │   └── InputBar.vue         # 底部输入栏（含发送/暂停按钮）
    │
    └── SettingsView.vue         # /settings 设置页
        ├── PresetSelector.vue   # 预设下拉 + [新建][删除][保存]
        ├── ModelSelector.vue    # Model 下拉 + [拉取]
        └── ResponseFormatInput.vue # response_format 大文本输入
```

---

## 4. Pinia Store

### 4.1 useSettingsStore

```js
state: {
  presets:          [],           // 预设列表（GET /api/settings）
  activePresetId:   null,         // 当前选中预设 ID
  apiUrl:           '',           // 当前 API URL
  apiKey:           '',           // 当前 API Key（脱敏显示）
  model:            '',           // 当前 model
  responseFormat:   '',           // response_format JSON
  availableModels:  [],           // 拉取到的 models 列表
}

actions: {
  loadPresets()                  // GET  /api/settings
  selectPreset(id)               // 切换预设 → 填充各字段
  createPreset(name)             // POST /api/settings
  savePreset()                   // PUT  /api/settings/:id
  deletePreset(id)               // DELETE /api/settings/:id
  fetchModels()                  // ⚠️ 后端待新增 /api/models
}
```

### 4.2 useChatStore

```js
state: {
  conversations:  [],            // 对话列表
  activeConvId:   null,          // 当前对话 ID
  messages:       [],            // 当前对话消息
  isStreaming:    false,         // 是否 SSE 流式中
  abortController: null,         // 中断 SSE
  aiVersionIndex: 0,             // 当前 AI 回复版本索引
  aiVersions:     {},            // { messageId: [version1, ...] } ⚠️ 多版本
}

actions: {
  loadConversations()            // GET    /api/conversations
  createConversation()           // POST   /api/conversations
  deleteConversation(id)         // DELETE /api/conversations/:id
  renameConversation(id, title)  // ⚠️ 后端待新增 PUT /api/conversations/:id
  selectConversation(id)         // GET    /api/conversations/:id（含 messages）
  sendMessage(content)           // POST   /api/conversations/:id/chat → SSE
  stopStreaming()                // POST   /api/conversations/:id/stop
  editMessage(id, content)       // PUT    /api/conversations/:id/messages/:msgId
  replayMessage(id)              // POST   /api/conversations/:id/regenerate → SSE
  switchVersion(id, direction)   // 本地切换 aiVersions 索引
}
```

---

## 5. 页面布局

### 5.1 整体布局 (App.vue)

```
┌──────────┬───────────────────────────┐
│ Sidebar  │     <router-view>         │
│ 260px    │     flex: 1               │
│ bg:#f5f5 │     bg:#fff               │
└──────────┴───────────────────────────┘
```

### 5.2 对话页 (ChatView)

```
┌──────────┬───────────────────────────┐
│ 对话列表  │  WelcomeBanner（无对话时）  │
│          │  或 MessageList（有对话时） │
│ ·对话1   │  ┌───────────────────────┐│
│ ·对话2 ✓ │  │  AI 气泡（左，白底黑字）││
│ ·对话3   │  │  边框: #e8e8e8        ││
│          │  └───────────────────────┘│
│ [+新建]  │                          │
│          │        ┌───────────────┐  │
│          │        │ 用户气泡（右） │  │
│          │        │ 边框: #d5d5d5 │  │
│          │        └───────────────┘  │
│          │                          │
│          │  [编辑] [重放] [◀ ▶]     │
│          │                          │
│          │  ┌─────────────────────┐ │
│          │  │  输入消息...    [▶] │ │
│          │  └─────────────────────┘ │
└──────────┴───────────────────────────┘
```

**气泡规格**：
- 通用：圆角 12px，padding 12px 16px，max-width 70%，白底黑字
- 用户：右对齐（`margin-left: auto`），边框 `1px solid #d5d5d5`
- AI：左对齐（`margin-right: auto`），边框 `1px solid #e8e8e8`
- 操作按钮（仅 AI 最后一条）：浅灰 `#e8e8e8`，hover `#d5d5d5`

**输入栏**：
- 圆角 24px，边框 `1px solid #d5d5d5`，min-height 44px
- 发送按钮 ▶ 在输入栏内右侧，发送中变为 ⏸
- 发送 → `sendMessage`；暂停 → `stopStreaming`

### 5.3 设置页 (SettingsView)

```
┌──────────┬───────────────────────────┐
│          │  设置                     │
│          │                          │
│          │  预设：[▼ 预设名称] [新建][删除][保存]
│          │                          │
│ Sidebar  │  API URL    [____________]
│          │  API Key    [____________]
│          │                          │
│          │  Model      [▼ gpt-4o] [🔄拉取]
│          │                          │
│          │  response_format         │
│          │  ┌──────────────────────┐│
│          │  │ (等宽字体 textarea)  ││
│          │  │ min-height: 150px    ││
│          │  └──────────────────────┘│
└──────────┴───────────────────────────┘
```

---

## 6. API 映射

基于现有后端 API（`docs/API.md`），与前端交互映射：

| 前端操作 | API 调用 | 备注 |
|----------|----------|------|
| 加载预设列表 | `GET /api/settings` | api_key 脱敏返回 |
| 新建预设 | `POST /api/settings` | |
| 保存预设 | `PUT /api/settings/:id` | 空 key 不覆盖 |
| 删除预设 | `DELETE /api/settings/:id` | 不能删默认 |
| 拉取 Models | ⚠️ **后端待新增** | 用当前 apiUrl/apiKey 请求 |
| 加载对话列表 | `GET /api/conversations` | |
| 新建对话 | `POST /api/conversations` | |
| 删除对话 | `DELETE /api/conversations/:id` | 级联删除消息 |
| 重命名对话 | ⚠️ **后端待新增** `PUT /api/conversations/:id` | |
| 选择对话（加载消息） | `GET /api/conversations/:id` | data.messages |
| 发送消息 | `POST /api/conversations/:id/chat` → **SSE** | |
| 停止生成 | `POST /api/conversations/:id/stop` | |
| 编辑消息 | `PUT /api/conversations/:id/messages/:msgId` | 仅 user 消息 |
| 重新生成 | `POST /api/conversations/:id/regenerate` → **SSE** | |

### SSE 流式时序

```
前端                                后端
 │                                   │
 ├── POST /chat { content } ────────→│ 保存 user 消息
 │                                   │ 组装上下文 → 调 AI API
 │←── data: {"delta":"Hello"} ──────┤
 │←── data: {"delta":" world"} ─────┤
 │←── data: {"delta":"","done":true}┤ 写入 assistant 消息
 │                                   │
 [用户点 ⏸ 暂停]                     │
 ├── POST /stop ────────────────────→│ 设置 cancel
 │←── { code:0 } ───────────────────┤
 │←── data: {"stopped":true} ───────┤
```

---

## 7. 已知 Gap（需后端配合 / 待确认）

| # | Gap | 影响 | 建议 |
|---|-----|------|------|
| 1 | **Model 拉取接口不存在** | 设置页"拉取"按钮无对应 API | 后端新增 `POST /api/settings/models`（用当前 apiUrl/apiKey 发 `/v1/models` 请求） |
| 2 | **对话重命名接口** | Sidebar 右键重命名无 API | 后端新增 `PUT /api/conversations/:id` 更新 title |
| 3 | **多版本切换 vs regenerate 语义** | regenerate 是"删除旧 assistant → 重新生成"，不保留旧版本。用户期望 ← → 在多版本间切换 | MVP 阶段先不实现多版本切换，regenerate 后旧回复丢失。后续可扩展到 `aiVersions` 本地缓存 |
| 4 | **编辑 AI 消息** | API 限制"仅可编辑 role:user 的消息" | MVP 阶段编辑按钮仅对 user 消息生效；AI 气泡暂不显示编辑按钮 |

---

## 8. 文件结构（新增/修改）

```
frontend/src/
├── App.vue                          # [修改] 加入 Sidebar + <router-view>
├── router/index.js                  # [修改] 新增 /settings 路由
│
├── views/
│   ├── ChatView.vue                 # [新增] 对话主页
│   └── SettingsView.vue             # [新增] 设置页
│
├── components/
│   ├── Sidebar.vue                  # [新增] 对话列表侧栏
│   ├── ConversationItem.vue         # [新增] 对话列表项
│   ├── MessageList.vue              # [新增] 消息滚动区
│   ├── MessageBubble.vue            # [新增] 单条气泡
│   ├── MessageActions.vue           # [新增] 编辑/重放/切换
│   ├── InputBar.vue                 # [新增] 底部输入栏
│   ├── WelcomeBanner.vue            # [新增] 欢迎引导
│   ├── PresetSelector.vue           # [新增] 预设选择器
│   ├── ModelSelector.vue            # [新增] Model 选择器
│   └── ResponseFormatInput.vue      # [新增] response_format 输入
│
├── stores/
│   ├── settings.js                  # [新增] useSettingsStore
│   └── chat.js                      # [新增] useChatStore
│
├── api/
│   ├── settings.js                  # [修改] 补齐 CRUD + fetchModels
│   ├── conversations.js             # [修改] 补齐 rename/regenerate/stop
│   └── sse.js                       # [修改] 暴露 abort 能力
│
└── main.js                          # [修改] 注册 Pinia stores
```

---

## 9. 非功能需求

| 项 | 要求 |
|----|------|
| 响应式 | 仅桌面端（≥1024px），不要求移动端适配 |
| 错误处理 | 统一判断 `code === 0`，非零 `alert(message)` |
| 加载态 | 消息发送中显示骨架/闪烁光标，预设列表加载中显示 loading |
| 空状态 | 无对话时显示 WelcomeBanner，无预设时显示引导提示 |
| 浏览器 | Chrome/Edge/Firefox 最新两版 |
