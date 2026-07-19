# Chat 前端 MVP 设计文档

> 日期：2026-07-19 · 分支：`develop` · 方案：纯 Vue 3 + Pinia + 手写 CSS

---

## 1. 概述

**产品定位**：AI 对话客户端（类 ChatGPT），MVP 阶段仅 Web 端。

**MVP 范围**：
- **API 设置弹窗** — 预设管理、API URL/Key 配置、Model 下拉 + 拉取、response_format
- **对话页** — 对话列表侧边栏、消息气泡流、SSE 流式、编辑用户消息

**MVP 明确不做**：
- AI 消息的编辑、重放、多版本切换
- 对话重命名
- 暗色主题、移动端适配、Electron 打包

**UI 风格**：类 ChatGPT 简约亮色主题 — 主色 `#fff`，辅助色白偏灰（`#f5f5f5` / `#e8e8e8`），灰色线边框（`#d5d5d5`），按钮统一浅灰色。

---

## 2. 路由

仅一个路由：

| 路径 | 视图 | 说明 |
|------|------|------|
| `/` | `ChatView` | 对话页（默认首页） |

设置页不再作为独立路由，而是以**模态弹窗**形式从 TopBar 触发。

---

## 3. 组件树

```
App.vue
├── TopBar.vue                    # 顶部栏
│   └── [⚙ 设置] 按钮            # → 打开 SettingsModal
│
├── Sidebar.vue                   # 左侧对话列表栏（260px）
│   ├── [＋ 新建对话] 按钮
│   └── ConversationItem.vue × N  # 对话项（选中高亮、右键删除）
│
├── SettingsModal.vue             # 设置弹窗（v-if 控制显隐）
│   ├── PresetSelector.vue        # 预设下拉 + [新建][删除][保存]
│   ├── [API URL 输入栏]
│   ├── [API Key 输入栏]
│   ├── ModelSelector.vue         # Model 下拉 + [拉取]
│   └── ResponseFormatInput.vue   # response_format 大文本输入
│
└── <router-view>
    └── ChatView.vue              # / 对话主页
        ├── WelcomeBanner.vue     # 无对话时的引导欢迎语
        ├── MessageList.vue       # 消息滚动区域
        │   └── MessageBubble.vue # 单条气泡（user 右 / assistant 左）
        │       └── [✎ 编辑]      # 仅最新一条 user 消息的气泡内
        └── InputBar.vue          # 底部输入栏（含发送 ▶ / 暂停 ⏸）
```

---

## 4. Pinia Store

### 4.1 useSettingsStore

```js
state: {
  presets:          [],           // GET /api/settings
  activePresetId:   null,         // 当前选中预设 ID
  apiUrl:           '',           // 当前 API URL
  apiKey:           '',           // 当前 API Key（脱敏显示，保存时传明文）
  model:            '',           // 当前 model
  responseFormat:   '',           // response_format JSON 字符串
  availableModels:  [],           // 拉取到的 models 列表
}

actions: {
  loadPresets()                  // GET  /api/settings
  selectPreset(id)               // 切换预设 → 填充各字段
  createPreset(name)             // POST /api/settings
  savePreset()                   // PUT  /api/settings/:id
  deletePreset(id)               // DELETE /api/settings/:id
  fetchModels()                  // ⚠️ 后端待新增
}
```

### 4.2 useChatStore

```js
state: {
  conversations:  [],            // GET /api/conversations
  activeConvId:   null,          // 当前对话 ID
  messages:       [],            // 当前对话消息（GET /api/conversations/:id）
  isStreaming:    false,         // SSE 流式进行中
  abortController: null,         // 中断 SSE
}

actions: {
  loadConversations()            // GET    /api/conversations
  createConversation()           // POST   /api/conversations
  deleteConversation(id)         // DELETE /api/conversations/:id
  selectConversation(id)         // GET    /api/conversations/:id（含 messages）
  sendMessage(content)           // POST   /api/conversations/:id/chat → SSE 流式
  stopStreaming()                // POST   /api/conversations/:id/stop
  editMessage(id, content)       // PUT    /api/conversations/:id/messages/:msgId
                                 //       仅允许最新一条 user 消息
}
```

> `editMessage` 编辑成功后，后端自动删除该消息之后的所有消息（截断）。
> 前端收到响应后需重新加载 messages 或本地同步截断。

---

## 5. 页面布局

### 5.1 整体布局 (App.vue)

```
┌──────────────────────────────────────────┐
│  TopBar                              [⚙] │  height: 48px, bg: #fafafa, border-bottom
├──────────┬───────────────────────────────┤
│ Sidebar  │     <router-view>             │
│ 260px    │     flex: 1                   │
│ bg:#f5f5 │     bg:#fff                   │
└──────────┴───────────────────────────────┘
```

### 5.2 对话页 (ChatView)

```
┌──────────┬───────────────────────────────┐
│ 对话列表  │  WelcomeBanner（无对话时）      │
│          │  或 MessageList（有对话时）     │
│ ·对话1   │  ┌───────────────────────────┐│
│ ·对话2 ✓ │  │ AI 气泡（左对齐）          ││
│ ·对话3   │  │ 白底黑字 边框 #e8e8e8     ││
│          │  └───────────────────────────┘│
│ [+新建]  │                               │
│          │       ┌──────────────────┐    │
│          │       │ 用户气泡（右对齐）│    │
│          │       │ 边框 #d5d5d5     │    │
│          │       │ [✎ 编辑]         │    │ ← 仅最新一条 user 消息
│          │       └──────────────────┘    │
│          │                               │
│          │  ┌───────────────────────────┐│
│          │  │  输入消息...         [▶]  ││
│          │  └───────────────────────────┘│
└──────────┴───────────────────────────────┘
```

**气泡规格**：
| 属性 | 用户 | AI |
|------|------|-----|
| 对齐 | 右 (`margin-left: auto`) | 左 (`margin-right: auto`) |
| 背景 | `#fff` | `#fff` |
| 边框 | `1px solid #d5d5d5` | `1px solid #e8e8e8` |
| 圆角 | 12px | 12px |
| padding | 12px 16px | 12px 16px |
| max-width | 70% | 70% |
| 编辑按钮 | 仅最新一条显示 | 无 |

**编辑按钮**（仅出现在最新一条 user 消息气泡右下角）：
- 浅灰色文字 `✎ 编辑`，字体 12px
- hover 变深灰
- 点击 → 气泡内容变为可编辑 textarea → 显示 [保存] [取消]

**输入栏**：
- 圆角 24px，边框 `1px solid #d5d5d5`，min-height 44px
- 发送按钮 ▶ 在输入栏内部右侧
- 发送中 ▶ 变为 ⏸（暂停），点击调用 `stopStreaming()`

### 5.3 设置弹窗 (SettingsModal)

```
┌──────────────────────────────────────────┐
│  ⚙ 设置                             [✕] │  ← 标题栏
│                                          │
│  预设：[▼ 预设名称    ] [新建][删除][保存] │
│                                          │
│  API URL    [___________________________]│
│  API Key    [___________________________]│
│                                          │
│  Model      [▼ gpt-4o         ] [🔄拉取] │
│                                          │
│  response_format                         │
│  ┌──────────────────────────────────────┐│
│  │  (等宽字体 textarea, min-height 120px)││
│  └──────────────────────────────────────┘│
└──────────────────────────────────────────┘
```

- 模态弹窗，居中显示，宽度约 560px
- 背景半透明遮罩 (`rgba(0,0,0,0.3)`)
- 弹窗白底，圆角 12px，padding 24px
- 点击遮罩或 ✕ 关闭（关闭时若未保存，丢弃修改）

---

## 6. API 映射

基于现有后端 API（`docs/API.md`）：

| 前端操作 | API 调用 | 备注 |
|----------|----------|------|
| 加载预设列表 | `GET /api/settings` | api_key 脱敏返回 `sk-a****` |
| 新建预设 | `POST /api/settings` | |
| 保存预设 | `PUT /api/settings/:id` | 空 key 不覆盖原密钥 |
| 删除预设 | `DELETE /api/settings/:id` | 不能删除默认配置 |
| 拉取 Models | ⚠️ **后端待新增** | 用当前 apiUrl/apiKey 请求 `/v1/models` |
| 加载对话列表 | `GET /api/conversations` | |
| 新建对话 | `POST /api/conversations` | title 选填，默认"新对话" |
| 删除对话 | `DELETE /api/conversations/:id` | 级联删除消息 |
| 选择对话（加载消息）| `GET /api/conversations/:id` | `data.messages[]` |
| 发送消息 | `POST /api/conversations/:id/chat` → **SSE** | |
| 停止生成 | `POST /api/conversations/:id/stop` | |
| 编辑消息 | `PUT /api/conversations/:id/messages/:msgId` | 仅 user 消息，编辑后截断 |

### SSE 流式时序

```
前端                                后端
 │                                   │
 ├── POST /chat { content } ────────→│ 保存 user 消息 → 调 AI API
 │←── data: {"delta":"Hello"} ──────┤
 │←── data: {"delta":" world"} ─────┤
 │←── data: {"delta":"","done":true}┤ 写入 assistant 消息
 │                                   │
 [用户点击 ⏸ 暂停]                    │
 ├── POST /stop ────────────────────→│ 设置取消信号
 │←── { code:0 } ───────────────────┤
 │←── data: {"stopped":true} ───────┤
```

### 编辑消息时序

```
前端                                    后端
 │                                       │
 ├── PUT /messages/:msgId {content} ────→│ 更新 content
 │                                       │ 删除该消息之后的所有消息
 │←── { code:0, data: { id, ... } } ────┤
 │                                       │
 │  ← 前端重新 GET /conversations/:id    │  或本地截断 messages 数组
```

---

## 7. 已知 Gap（需后端配合）

| # | Gap | 影响 | 建议 |
|---|-----|------|------|
| 1 | **Model 拉取接口不存在** | 设置弹窗"拉取"按钮无对应 API | 后端新增 `POST /api/settings/models`：接收 `{apiUrl, apiKey}` → 转发 `GET {apiUrl}/v1/models` → 返回 models 列表 |
| 2 | **对话重命名接口** | MVP 暂不做重命名功能 | 此 Gap 无影响——MVP 不包含重命名 |

---

## 8. 文件结构

```
frontend/src/
├── App.vue                          # [修改] 加入 TopBar + Sidebar + SettingsModal + <router-view>
├── router/index.js                  # [不改] 保持仅 "/" 路由
│
├── views/
│   └── ChatView.vue                 # [新增] 对话主页
│
├── components/
│   ├── TopBar.vue                   # [新增] 顶部栏（含设置按钮）
│   ├── Sidebar.vue                  # [新增] 对话列表侧栏
│   ├── ConversationItem.vue         # [新增] 对话列表项
│   ├── SettingsModal.vue            # [新增] 设置弹窗（整页遮罩 + 居中面板）
│   ├── PresetSelector.vue           # [新增] 预设选择器（下拉 + 新建/删除/保存）
│   ├── ModelSelector.vue            # [新增] Model 选择器（下拉 + 拉取按钮）
│   ├── ResponseFormatInput.vue      # [新增] response_format textarea
│   ├── MessageList.vue              # [新增] 消息滚动区
│   ├── MessageBubble.vue            # [新增] 单条气泡（含编辑按钮逻辑）
│   ├── InputBar.vue                 # [新增] 底部输入栏（发送/暂停）
│   └── WelcomeBanner.vue            # [新增] 欢迎引导
│
├── stores/
│   ├── settings.js                  # [新增] useSettingsStore
│   └── chat.js                      # [新增] useChatStore
│
├── api/
│   ├── settings.js                  # [修改] 补齐 CRUD + fetchModels
│   ├── conversations.js             # [修改] 补齐 stop
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
| 加载态 | SSE 接收中显示闪烁光标；预设列表加载中显示 loading 文字 |
| 空状态 | 无对话时显示 WelcomeBanner；无预设时下拉菜单显示"暂无预设，请新建" |
| 浏览器 | Chrome / Edge / Firefox 最新两版 |
