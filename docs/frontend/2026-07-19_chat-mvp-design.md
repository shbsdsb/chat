# Chat MVP 前端设计文档

> 日期：2025-07-16 | 版本：v1.0 | 状态：已确认

---

## 1. 概述

Chat 是一个 AI 对话客户端，基于 Vue 3 + Vite + Pinia + Vue Router，后端为 Flask + SQLite。MVP 阶段聚焦两个核心页面：**API 设置页** 和 **对话页**。

### 技术栈

| 层 | 技术 |
|----|------|
| 框架 | Vue 3（Composition API） |
| 构建 | Vite 5 |
| 状态 | Pinia |
| 路由 | Vue Router 4 |
| HTTP | Axios |
| 桌面 | Electron（MVP 暂不启用） |
| 样式 | 手写 CSS，零 UI 框架依赖 |

### UI 风格

- 类 ChatGPT 简约风格
- 仅亮色主题
- 主色：白色（`#ffffff`）
- 辅助色：白偏灰（`#f5f5f5`, `#fafafa`）
- 边框色：浅灰（`#e0e0e0`, `#d5d5d5`, `#e8e8e8`）
- 所有按钮主题色：浅灰色系

---

## 2. 路由设计

| 路径 | 视图 | 说明 |
|------|------|------|
| `/` | `ChatView` | 对话页（默认首页） |
| `/settings` | `SettingsView` | API 设置页 |

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

## 4. Pinia Store 设计

### 4.1 useSettingsStore

管理 API 预设和当前生效的配置。

```js
state: {
  presets:          [],          // 预设列表（从后端加载）
  activePresetId:   null,        // 当前选中的预设 ID
  apiUrl:           '',          // 当前 API URL
  apiKey:           '',          // 当前 API Key
  model:            '',          // 当前 model
  responseFormat:   '',          // 当前 response_format (JSON 字符串)
  availableModels:  [],          // 拉取到的 model 列表
}

actions: {
  loadPresets(),                // GET /api/settings
  selectPreset(id),             // 切换预设，同步填充各字段
  createPreset(name),           // POST /api/settings
  savePreset(),                 // PUT /api/settings/:id
  deletePreset(id),             // DELETE /api/settings/:id
  fetchModels(),                // POST /api/settings/models
}
```

### 4.2 useChatStore

管理对话列表、当前对话、消息和 SSE 流。

```js
state: {
  conversations:    [],          // 对话列表
  activeConvId:     null,        // 当前对话 ID
  messages:         [],          // 当前对话的消息列表
  isStreaming:      false,       // 是否正在 SSE 流式接收
  abortController:  null,        // 用于取消 SSE

  // AI 多版本回复
  aiVersionIndex:   0,           // 当前查看的 AI 回复版本（0-based）
  aiVersions:       {},          // { messageId: [version1, version2, ...] }
}

actions: {
  loadConversations(),           // GET /api/conversations
  createConversation(),          // POST /api/conversations
  deleteConversation(id),        // DELETE /api/conversations/:id
  renameConversation(id, title), // PUT /api/conversations/:id
  selectConversation(id),        // 切换对话 + GET /api/conversations/:id
  sendMessage(content),          // POST /api/conversations/:id/chat → SSE
  stopStreaming(),               // POST /api/conversations/:id/stop
  editMessage(id, content),      // PUT /api/conversations/:id/messages/:msgId
  replayMessage(id),             // POST /api/conversations/:id/regenerate → SSE
  switchVersion(id, dir),        // ← → 切换 AI 回复版本
}
```

---

## 5. 页面布局

### 5.1 整体布局（App.vue）

```
┌──────────┬───────────────────────────────┐
│          │                               │
│  Sidebar │      <router-view>            │
│  260px   │        flex: 1                │
│          │                               │
└──────────┴───────────────────────────────┘
```

- **Sidebar**：固定 260px，浅灰背景（`#f5f5f5`），始终可见
- **主区域**：`flex: 1`，白色背景

### 5.2 对话页（ChatView）

```
┌──────────┬───────────────────────────────┐
│          │  WelcomeBanner（无对话时）      │
│          │                               │
│ 对话列表  │  ┌─────────────────────────┐  │
│          │  │  用户气泡（右对齐）       │  │
│  ·对话1   │  │  ┌───────────────────┐  │  │
│  ·对话2 ✓ │  │  │ 白底黑字 灰边框    │  │  │
│  ·对话3   │  │  └───────────────────┘  │  │
│          │  │                         │  │
│  [+新建]  │  │  AI 气泡（左对齐）        │  │
│          │  │  ┌───────────────────┐  │  │
│          │  │  │ 白底黑字 灰边框    │  │  │
│          │  │  └───────────────────┘  │  │
│          │  │  [编辑] [重放] [← →]    │  │
│          │  └─────────────────────────┘  │
│          │                               │
│          │  ┌─────────────────────────┐  │
│          │  │  输入框...     [▶/⏸]   │  │
│          │  └─────────────────────────┘  │
└──────────┴───────────────────────────────┘
```

**气泡样式**：
- 通用：白底黑字，圆角 12px，边框 `1px solid #e0e0e0`，padding 12px 16px，max-width 70%
- 用户气泡：`margin-left: auto`（右对齐），边框色 `#d5d5d5`
- AI 气泡：`margin-right: auto`（左对齐），边框色 `#e8e8e8`

**AI 最后一条消息操作按钮**（浅灰色）：
- **编辑**：自由编辑气泡内文字
- **重放**：让 AI 重新生成回复
- **← → 切换**：在 AI 多个输出版本间切换

**输入栏**：
- 圆角 24px，边框 `1px solid #d5d5d5`，高度自适应（min 44px）
- 发送按钮 ▶ 在输入栏内部右侧
- 发送中变为停止按钮 ⏸，可随时暂停 AI 输出
- 均为浅灰色主题

### 5.3 设置页（SettingsView）

```
┌──────────┬───────────────────────────────┐
│          │  设置                          │
│          │                               │
│          │  预设：[▼ 预设名称] [新建][删除][保存] │
│  Sidebar │                               │
│          │  API URL    [______________]  │
│          │                               │
│          │  API Key    [______________]  │
│          │                               │
│          │  Model      [▼ gpt-4o] [🔄拉取] │
│          │                               │
│          │  response_format              │
│          │  ┌─────────────────────────┐  │
│          │  │  (较大的文本输入区)      │  │
│          │  │                         │  │
│          │  └─────────────────────────┘  │
└──────────┴───────────────────────────────┘
```

**预设栏**：下拉菜单 + 新建 + 删除 + 保存，水平排列，浅灰边框按钮

**Model 栏**：下拉选择 + 🔄 拉取按钮（触发 `fetchModels`，从 API 获取可用模型列表填充下拉菜单）

**response_format**：textarea，高度约 150px，等宽字体

---

## 6. SSE 流式交互

```
1. POST /api/conversations/:id/chat
   Body: { "content": "用户消息" }
   → 后端追加 user message，返回 SSE stream

2. SSE 事件：
   data: {"delta": "Hello"}     → 追加到当前 assistant 消息
   data: {"delta": " world"}    → 继续追加
   ...
   data: {"done": true}         → 流结束，消息完成

3. 用户点击 ⏸（停止）：
   → POST /api/conversations/:id/stop
   → SSE 返回 {"stopped": true} 后关闭

4. 用户点击 🔄（重放）：
   → POST /api/conversations/:id/regenerate
   → 新 SSE stream，结果存入 aiVersions[id] 新版本
```

---

## 7. 前端 API 层

需补充的 API 调用函数：

### settings.js
| 函数 | 方法 | 路径 |
|------|------|------|
| `getSettings()` | GET | `/settings` |
| `createPreset(data)` | POST | `/settings` |
| `updatePreset(id, data)` | PUT | `/settings/:id` |
| `deletePreset(id)` | DELETE | `/settings/:id` |
| `fetchModels(apiUrl, apiKey)` | GET | `/settings/models` |

### conversations.js
| 函数 | 方法 | 路径 |
|------|------|------|
| `getConversations()` | GET | `/conversations` |
| `createConversation(title?)` | POST | `/conversations` |
| `getConversation(id)` | GET | `/conversations/:id` |
| `deleteConversation(id)` | DELETE | `/conversations/:id` |
| `renameConversation(id, title)` | PUT | `/conversations/:id` |
| `sendMessage(convId, content)` | POST (SSE) | `/conversations/:id/chat` |
| `editMessage(convId, msgId, content)` | PUT | `/conversations/:id/messages/:msgId` |
| `regenerate(convId)` | POST (SSE) | `/conversations/:id/regenerate` |
| `stopGeneration(convId)` | POST | `/conversations/:id/stop` |

---

## 8. 文件结构（目标）

```
frontend/src/
├── App.vue
├── main.js
├── api/
│   ├── index.js              # Axios 实例
│   ├── request.js            # 请求封装
│   ├── conversations.js      # 对话 API（需扩展）
│   ├── settings.js           # 设置 API（需扩展）
│   └── sse.js                # SSE 流处理（需扩展 abort）
├── router/
│   └── index.js              # 路由（需加 /settings）
├── stores/
│   ├── settings.js           # 新增：useSettingsStore
│   └── chat.js               # 新增：useChatStore
├── components/
│   ├── Sidebar.vue           # 新增
│   ├── ConversationItem.vue  # 新增
│   ├── MessageBubble.vue     # 新增
│   ├── MessageActions.vue    # 新增
│   ├── MessageList.vue       # 新增
│   ├── InputBar.vue          # 新增
│   ├── WelcomeBanner.vue     # 新增
│   ├── PresetSelector.vue    # 新增
│   ├── ModelSelector.vue     # 新增
│   └── ResponseFormatInput.vue # 新增
└── views/
    ├── Home.vue              # 改造为 ChatView（或重命名）
    └── SettingsView.vue      # 新增
```
