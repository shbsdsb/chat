# Chat MVP 前端实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 Chat AI 对话客户端 MVP 前端 — 设置页 + 对话页，类 ChatGPT 简约亮色风格，SSE 流式传输。

**Architecture:** Vue 3 Composition API + Pinia + Vue Router + 手写 CSS，零 UI 框架依赖。分 5 个模块依次实施，每个模块完成后 `npm run dev` 预览确认再继续。

**Tech Stack:** Vue 3.4, Pinia 2.1, Vue Router 4.3, Axios 1.7, Vite 5.4

## Global Constraints

- 仅亮色主题：主色 `#ffffff`，辅助色 `#f5f5f5`/`#fafafa`，边框 `#e0e0e0`/`#d5d5d5`/`#e8e8e8`
- 所有按钮浅灰色系
- 气泡：白底黑字，圆角 12px，max-width 70%
- 输入栏：圆角 24px，边框 `1px solid #d5d5d5`
- Sidebar：固定 260px，`#f5f5f5` 背景
- 命名：组件 PascalCase，Store camelCase（useXxxStore）
- 路由：`/` → ChatView，`/settings` → SettingsView
- 仅实施前端，后端 API 暂不开发（前端 mock 或连接现有后端骨架）
- 每个模块完成后必须 `npm run dev` 启动预览，用户确认后再继续

---

## File Map

```
frontend/src/
├── App.vue                      # [MODIFY] Sidebar + router-view 布局
├── main.js                      # [KEEP] 已配置 Pinia + Router
├── router/index.js              # [MODIFY] 加 /settings 路由
├── api/
│   ├── index.js                 # [MODIFY] 补导出
│   ├── request.js               # [KEEP] 已完善
│   ├── sse.js                   # [KEEP] 已完善
│   ├── conversations.js         # [MODIFY] 加 rename / editMessage
│   └── settings.js              # [MODIFY] 加 fetchModels
├── stores/
│   ├── settings.js              # [CREATE] useSettingsStore
│   └── chat.js                  # [CREATE] useChatStore
├── components/
│   ├── Sidebar.vue              # [CREATE]
│   ├── ConversationItem.vue     # [CREATE]
│   ├── MessageBubble.vue        # [CREATE]
│   ├── MessageActions.vue       # [CREATE]
│   ├── MessageList.vue          # [CREATE]
│   ├── InputBar.vue             # [CREATE]
│   ├── WelcomeBanner.vue        # [CREATE]
│   ├── PresetSelector.vue       # [CREATE]
│   ├── ModelSelector.vue        # [CREATE]
│   └── ResponseFormatInput.vue  # [CREATE]
└── views/
    ├── Home.vue                 # [REWRITE] → ChatView
    └── SettingsView.vue         # [CREATE]
```

---

### Task 1: 基础架构 — 路由 + App 布局 + Store + API 补全

**Files:**
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/api/index.js`
- Modify: `frontend/src/api/conversations.js`
- Modify: `frontend/src/api/settings.js`
- Create: `frontend/src/stores/settings.js`
- Create: `frontend/src/stores/chat.js`

**Interfaces:**
- Produces: `useSettingsStore` (loadPresets, selectPreset, createPreset, savePreset, deletePreset, fetchModels), `useChatStore` (loadConversations, createConversation, deleteConversation, renameConversation, selectConversation, sendMessage, stopStreaming, editMessage, replayMessage, switchVersion), 路由 `/` 和 `/settings`

- [ ] **Step 1: 扩展路由 — 添加 /settings**

`frontend/src/router/index.js` — 替换为：

```js
import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    name: "Chat",
    component: () => import("@/views/Home.vue"),
  },
  {
    path: "/settings",
    name: "Settings",
    component: () => import("@/views/SettingsView.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
```

- [ ] **Step 2: 改造 App.vue — Sidebar + router-view 布局**

`frontend/src/App.vue` — 替换为：

```vue
<template>
  <div id="app" class="app-layout">
    <Sidebar />
    <main class="main-area">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import Sidebar from "@/components/Sidebar.vue";
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: #333;
  background: #fff;
}

.app-layout {
  display: flex;
  height: 100%;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  overflow: hidden;
}
</style>
```

- [ ] **Step 3: 创建 Sidebar 骨架组件**

`frontend/src/components/Sidebar.vue` — 创建：

```vue
<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <button class="btn-new-chat" @click="handleNewChat">+ 新建对话</button>
    </div>
    <div class="sidebar-list">
      <ConversationItem
        v-for="conv in chatStore.conversations"
        :key="conv.id"
        :conversation="conv"
        :active="conv.id === chatStore.activeConvId"
        @select="chatStore.selectConversation(conv.id)"
        @delete="chatStore.deleteConversation(conv.id)"
        @rename="(title) => chatStore.renameConversation(conv.id, title)"
      />
    </div>
    <div class="sidebar-footer">
      <router-link to="/settings" class="btn-settings">设置</router-link>
    </div>
  </aside>
</template>

<script setup>
import { useChatStore } from "@/stores/chat";
import ConversationItem from "@/components/ConversationItem.vue";

const chatStore = useChatStore();

function handleNewChat() {
  chatStore.createConversation();
}
</script>

<style scoped>
.sidebar {
  width: 260px;
  min-width: 260px;
  height: 100%;
  background: #f5f5f5;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e0e0e0;
}

.sidebar-header {
  padding: 12px;
}

.btn-new-chat {
  width: 100%;
  padding: 8px 16px;
  border: 1px solid #d5d5d5;
  border-radius: 8px;
  background: #fff;
  color: #333;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-new-chat:hover {
  background: #e8e8e8;
}

.sidebar-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 8px;
}

.sidebar-footer {
  padding: 12px;
  border-top: 1px solid #e0e0e0;
}

.btn-settings {
  display: block;
  text-align: center;
  padding: 8px;
  border: 1px solid #d5d5d5;
  border-radius: 8px;
  background: #fff;
  color: #333;
  font-size: 13px;
  text-decoration: none;
  cursor: pointer;
}
.btn-settings:hover {
  background: #e8e8e8;
}
</style>
```

- [ ] **Step 4: 创建 ConversationItem 组件**

`frontend/src/components/ConversationItem.vue` — 创建：

```vue
<template>
  <div
    class="conv-item"
    :class="{ active }"
    @click="$emit('select')"
    @contextmenu.prevent="showMenu = true"
  >
    <span class="conv-title">{{ conversation.title }}</span>
    <div v-if="showMenu" class="context-menu">
      <button @click.stop="startRename">重命名</button>
      <button @click.stop="$emit('delete')">删除</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

const props = defineProps({
  conversation: { type: Object, required: true },
  active: { type: Boolean, default: false },
});

const emit = defineEmits(["select", "delete", "rename"]);

const showMenu = ref(false);

function startRename() {
  showMenu.value = false;
  const title = prompt("新名称", props.conversation.title);
  if (title && title.trim()) {
    emit("rename", title.trim());
  }
}

// 点击其他地方关闭菜单
document.addEventListener("click", () => {
  showMenu.value = false;
});
</script>

<style scoped>
.conv-item {
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  position: relative;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.conv-item:hover {
  background: #e8e8e8;
}
.conv-item.active {
  background: #fff;
  border: 1px solid #d5d5d5;
}

.conv-title {
  pointer-events: none;
}

.context-menu {
  position: absolute;
  top: 100%;
  left: 8px;
  background: #fff;
  border: 1px solid #d5d5d5;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  z-index: 10;
  overflow: hidden;
}
.context-menu button {
  display: block;
  width: 100%;
  padding: 6px 12px;
  border: none;
  background: #fff;
  color: #333;
  font-size: 13px;
  cursor: pointer;
  text-align: left;
}
.context-menu button:hover {
  background: #f5f5f5;
}
</style>
```

- [ ] **Step 5: 创建 useSettingsStore**

`frontend/src/stores/settings.js` — 创建：

```js
import { defineStore } from "pinia";
import * as settingsApi from "@/api/settings";

export const useSettingsStore = defineStore("settings", {
  state: () => ({
    presets: [],
    activePresetId: null,
    apiUrl: "",
    apiKey: "",
    model: "gpt-4o",
    responseFormat: "",
    availableModels: [],
  }),

  actions: {
    async loadPresets() {
      this.presets = await settingsApi.list();
      if (!this.activePresetId && this.presets.length > 0) {
        const def = this.presets.find((p) => p.is_default) || this.presets[0];
        this.selectPreset(def.id);
      }
    },

    selectPreset(id) {
      const preset = this.presets.find((p) => p.id === id);
      if (!preset) return;
      this.activePresetId = preset.id;
      this.apiUrl = preset.api_url;
      this.apiKey = preset.api_key;
      this.model = preset.model;
      this.responseFormat = preset.response_format;
    },

    async createPreset(name) {
      const preset = await settingsApi.create({
        name,
        api_url: "https://api.openai.com/v1",
        api_key: "",
        model: "gpt-4o",
        response_format: "text",
        temperature: 0.7,
        max_tokens: 4096,
      });
      this.presets.push(preset);
      this.selectPreset(preset.id);
    },

    async savePreset() {
      if (!this.activePresetId) return;
      const updated = await settingsApi.update(this.activePresetId, {
        api_url: this.apiUrl,
        api_key: this.apiKey,
        model: this.model,
        response_format: this.responseFormat,
      });
      const idx = this.presets.findIndex((p) => p.id === this.activePresetId);
      if (idx !== -1) this.presets[idx] = updated;
    },

    async deletePreset(id) {
      await settingsApi.remove(id);
      this.presets = this.presets.filter((p) => p.id !== id);
      if (this.activePresetId === id) {
        this.activePresetId = null;
        if (this.presets.length > 0) {
          this.selectPreset(this.presets[0].id);
        }
      }
    },

    async fetchModels() {
      const data = await settingsApi.fetchModels(this.apiUrl, this.apiKey);
      this.availableModels = data || [];
    },
  },
});
```

- [ ] **Step 6: 创建 useChatStore**

`frontend/src/stores/chat.js` — 创建：

```js
import { defineStore } from "pinia";
import * as conversationsApi from "@/api/conversations";
import { sse } from "@/api/sse";

export const useChatStore = defineStore("chat", {
  state: () => ({
    conversations: [],
    activeConvId: null,
    messages: [],
    isStreaming: false,
    abortController: null,
    aiVersionIndex: 0,
    aiVersions: {},
  }),

  actions: {
    async loadConversations() {
      this.conversations = await conversationsApi.list();
    },

    async createConversation() {
      const conv = await conversationsApi.create();
      this.conversations.unshift(conv);
      this.selectConversation(conv.id);
    },

    async deleteConversation(id) {
      await conversationsApi.remove(id);
      this.conversations = this.conversations.filter((c) => c.id !== id);
      if (this.activeConvId === id) {
        this.activeConvId = null;
        this.messages = [];
      }
    },

    async renameConversation(id, title) {
      const updated = await conversationsApi.rename(id, title);
      const idx = this.conversations.findIndex((c) => c.id === id);
      if (idx !== -1) this.conversations[idx] = updated;
    },

    async selectConversation(id) {
      this.activeConvId = id;
      this.aiVersionIndex = 0;
      const data = await conversationsApi.detail(id);
      this.messages = data.messages || [];
    },

    sendMessage(content) {
      if (!this.activeConvId || this.isStreaming) return;

      // 追加 user 消息
      const userMsg = {
        id: "temp-" + Date.now(),
        role: "user",
        content,
        created_at: new Date().toISOString(),
      };
      this.messages.push(userMsg);

      // 准备 assistant 占位
      const assistantMsg = {
        id: "temp-" + (Date.now() + 1),
        role: "assistant",
        content: "",
        created_at: new Date().toISOString(),
      };
      this.messages.push(assistantMsg);
      this.isStreaming = true;

      const es = sse(`/conversations/${this.activeConvId}/chat`, {
        method: "POST",
        body: JSON.stringify({ content }),
        onMessage: (chunk) => {
          if (chunk.stopped) {
            this.isStreaming = false;
            return;
          }
          if (chunk.delta) {
            const last = this.messages[this.messages.length - 1];
            if (last && last.role === "assistant") {
              last.content += chunk.delta;
            }
          }
          if (chunk.done) {
            this.isStreaming = false;
          }
        },
        onError: (err) => {
          this.isStreaming = false;
          console.error("SSE error:", err);
        },
        onDone: () => {
          this.isStreaming = false;
        },
      });

      this.abortController = es;
    },

    stopStreaming() {
      if (this.abortController) {
        conversationsApi.stopGeneration(this.activeConvId);
        this.abortController.close();
        this.abortController = null;
      }
      this.isStreaming = false;
    },

    async editMessage(id, content) {
      const updated = await conversationsApi.editMessage(this.activeConvId, id, content);
      // 编辑后截断：移除该消息之后的所有消息
      const idx = this.messages.findIndex((m) => m.id === id);
      if (idx !== -1) {
        this.messages[idx] = updated;
        this.messages = this.messages.slice(0, idx + 1);
      }
    },

    replayMessage(id) {
      const assistantMsg = this.messages.find((m) => m.id === id && m.role === "assistant");
      if (!assistantMsg || this.isStreaming) return;

      // 初始化版本管理
      if (!this.aiVersions[id]) {
        this.aiVersions[id] = [assistantMsg.content];
        this.aiVersionIndex = 0;
      }

      this.isStreaming = true;
      const newContent = { value: "" };

      const es = sse(`/conversations/${this.activeConvId}/regenerate`, {
        method: "POST",
        body: JSON.stringify({}),
        onMessage: (chunk) => {
          if (chunk.stopped) {
            this.isStreaming = false;
            return;
          }
          if (chunk.delta) {
            newContent.value += chunk.delta;
            assistantMsg.content = newContent.value;
          }
          if (chunk.done) {
            // 保存新版本
            this.aiVersions[id].push(newContent.value);
            this.aiVersionIndex = this.aiVersions[id].length - 1;
            this.isStreaming = false;
          }
        },
        onError: (err) => {
          this.isStreaming = false;
          console.error("Replay error:", err);
        },
        onDone: () => {
          this.isStreaming = false;
        },
      });

      this.abortController = es;
    },

    switchVersion(id, dir) {
      const versions = this.aiVersions[id];
      if (!versions || versions.length <= 1) return;

      const newIdx = this.aiVersionIndex + dir;
      if (newIdx < 0 || newIdx >= versions.length) return;

      this.aiVersionIndex = newIdx;
      const msg = this.messages.find((m) => m.id === id);
      if (msg) {
        msg.content = versions[newIdx];
      }
    },
  },
});
```

- [ ] **Step 7: 补全 API 层 — conversations.js**

`frontend/src/api/conversations.js` — 在文件末尾追加：

```js
export function rename(id, title) {
  return http.put(`/conversations/${id}`, { title });
}

export function editMessage(convId, msgId, content) {
  return http.put(`/conversations/${convId}/messages/${msgId}`, { content });
}

export function stopGeneration(convId) {
  return http.post(`/conversations/${convId}/stop`);
}
```

- [ ] **Step 8: 补全 API 层 — settings.js**

`frontend/src/api/settings.js` — 在文件末尾追加：

```js
export function fetchModels(apiUrl, apiKey) {
  return http.get("/settings/models", {
    params: { api_url: apiUrl, api_key: apiKey },
  });
}
```

- [ ] **Step 9: 创建占位视图 — SettingsView.vue**

`frontend/src/views/SettingsView.vue` — 创建骨架（Task 2 会完善）：

```vue
<template>
  <div class="settings-page">
    <h2>设置</h2>
    <p>设置页面将在下一步完善</p>
  </div>
</template>

<script setup>
</script>

<style scoped>
.settings-page {
  padding: 24px;
}
</style>
```

- [ ] **Step 10: 改造 Home.vue 为 ChatView 骨架**

`frontend/src/views/Home.vue` — 替换为：

```vue
<template>
  <div class="chat-view">
    <WelcomeBanner v-if="!chatStore.activeConvId" />
    <div v-else class="chat-content">
      <MessageList />
      <InputBar />
    </div>
  </div>
</template>

<script setup>
import { useChatStore } from "@/stores/chat";
import WelcomeBanner from "@/components/WelcomeBanner.vue";
import MessageList from "@/components/MessageList.vue";
import InputBar from "@/components/InputBar.vue";

const chatStore = useChatStore();
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}
</style>
```

- [ ] **Step 11: 创建 WelcomeBanner 骨架**

`frontend/src/components/WelcomeBanner.vue` — 创建：

```vue
<template>
  <div class="welcome">
    <h1>Chat</h1>
    <p>选择一个对话开始，或创建一个新对话</p>
    <button class="btn-start" @click="chatStore.createConversation()">开始新对话</button>
  </div>
</template>

<script setup>
import { useChatStore } from "@/stores/chat";
const chatStore = useChatStore();
</script>

<style scoped>
.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
}
.welcome h1 {
  font-size: 28px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}
.welcome p {
  font-size: 15px;
  margin-bottom: 24px;
}
.btn-start {
  padding: 10px 24px;
  border: 1px solid #d5d5d5;
  border-radius: 8px;
  background: #fff;
  color: #333;
  font-size: 15px;
  cursor: pointer;
}
.btn-start:hover {
  background: #f5f5f5;
}
</style>
```

- [ ] **Step 12: 创建 MessageList 和 InputBar 骨架**

`frontend/src/components/MessageList.vue`：

```vue
<template>
  <div class="message-list" ref="listRef">
    <template v-for="msg in chatStore.messages" :key="msg.id">
      <MessageBubble :message="msg" />
      <MessageActions
        v-if="isLastAssistant(msg)"
        :message="msg"
      />
    </template>
    <div v-if="chatStore.messages.length === 0" class="empty-hint">
      发送一条消息开始对话
    </div>
  </div>
</template>

<script setup>
import { watch, nextTick, ref } from "vue";
import { useChatStore } from "@/stores/chat";
import MessageBubble from "@/components/MessageBubble.vue";
import MessageActions from "@/components/MessageActions.vue";

const chatStore = useChatStore();
const listRef = ref(null);

function isLastAssistant(msg) {
  const msgs = chatStore.messages;
  if (msg.role !== "assistant") return false;
  // 是最后一条 assistant 消息
  for (let i = msgs.length - 1; i >= 0; i--) {
    if (msgs[i].role === "assistant") return msgs[i].id === msg.id;
  }
  return false;
}

watch(
  () => chatStore.messages.length,
  () => nextTick(() => {
    if (listRef.value) {
      listRef.value.scrollTop = listRef.value.scrollHeight;
    }
  })
);
</script>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
}
.empty-hint {
  text-align: center;
  color: #999;
  margin-top: 40px;
  font-size: 14px;
}
</style>
```

`frontend/src/components/InputBar.vue` — 骨架：

```vue
<template>
  <div class="input-bar">
    <div class="input-wrapper">
      <textarea
        v-model="input"
        class="input-field"
        placeholder="输入消息..."
        rows="1"
        @keydown.enter.exact.prevent="handleSend"
      ></textarea>
      <button class="btn-send" @click="handleSend">
        {{ chatStore.isStreaming ? '⏸' : '▶' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useChatStore } from "@/stores/chat";

const chatStore = useChatStore();
const input = ref("");

function handleSend() {
  if (chatStore.isStreaming) {
    chatStore.stopStreaming();
    return;
  }
  const text = input.value.trim();
  if (!text) return;
  chatStore.sendMessage(text);
  input.value = "";
}
</script>

<style scoped>
.input-bar {
  padding: 12px 24px 16px;
  border-top: 1px solid #f0f0f0;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  border: 1px solid #d5d5d5;
  border-radius: 24px;
  padding: 6px 6px 6px 16px;
  background: #fff;
}

.input-field {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: 15px;
  line-height: 1.5;
  max-height: 120px;
  padding: 4px 0;
  font-family: inherit;
}
.input-field::placeholder {
  color: #bbb;
}

.btn-send {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid #d5d5d5;
  background: #fff;
  color: #666;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.btn-send:hover {
  background: #f0f0f0;
}
</style>
```

- [ ] **Step 13: 创建 MessageBubble 和 MessageActions 骨架**

`frontend/src/components/MessageBubble.vue`：

```vue
<template>
  <div class="bubble-row" :class="message.role">
    <div class="bubble">
      <div class="bubble-text">{{ message.content }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  message: { type: Object, required: true },
});
</script>

<style scoped>
.bubble-row {
  display: flex;
  margin-bottom: 12px;
}
.bubble-row.user {
  justify-content: flex-end;
}
.bubble-row.assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid #e0e0e0;
  background: #fff;
  color: #333;
  font-size: 15px;
  line-height: 1.6;
}
.bubble-row.user .bubble {
  border-color: #d5d5d5;
}
.bubble-row.assistant .bubble {
  border-color: #e8e8e8;
}

.bubble-text {
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
```

`frontend/src/components/MessageActions.vue`：

```vue
<template>
  <div class="message-actions">
    <button class="action-btn" title="编辑" @click="$emit('edit', message.id)">✎</button>
    <button class="action-btn" title="重放" @click="$emit('replay', message.id)">🔄</button>
    <button class="action-btn" title="上一个版本" @click="$emit('prev', message.id)">←</button>
    <button class="action-btn" title="下一个版本" @click="$emit('next', message.id)">→</button>
  </div>
</template>

<script setup>
defineProps({
  message: { type: Object, required: true },
});
defineEmits(["edit", "replay", "prev", "next"]);
</script>

<style scoped>
.message-actions {
  display: flex;
  gap: 4px;
  padding-left: 4px;
  margin-bottom: 12px;
}

.action-btn {
  width: 28px;
  height: 28px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #fafafa;
  color: #888;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.action-btn:hover {
  background: #e8e8e8;
  color: #555;
}
</style>
```

- [ ] **Step 14: 启动预览验证**

```bash
cd frontend && npm run dev
```

验证要点：
- 页面加载，左侧 Sidebar 可见（260px，浅灰背景）
- 右侧显示 WelcomeBanner（欢迎语 + 开始新对话按钮）
- 点击"设置"可跳转到 `/settings`（占位页面）
- 浏览器控制台无报错

> ⏸️ **检查点 1：用户预览确认基础架构后，继续 Task 2。**

---

### Task 2: 设置页 — SettingsView + 子组件

**Files:**
- Rewrite: `frontend/src/views/SettingsView.vue`
- Create: `frontend/src/components/PresetSelector.vue`
- Create: `frontend/src/components/ModelSelector.vue`
- Create: `frontend/src/components/ResponseFormatInput.vue`

**Interfaces:**
- Consumes: `useSettingsStore` (presets, activePresetId, apiUrl, apiKey, model, responseFormat, availableModels, loadPresets, selectPreset, createPreset, savePreset, deletePreset, fetchModels)
- Produces: 完整的设置页面，可操作预设/API配置/Model/responseFormat

- [ ] **Step 1: 重写 SettingsView.vue**

`frontend/src/views/SettingsView.vue` — 替换为：

```vue
<template>
  <div class="settings-page">
    <h2 class="page-title">设置</h2>

    <div class="settings-section">
      <label class="section-label">预设</label>
      <PresetSelector />
    </div>

    <div class="settings-section">
      <label class="section-label">API URL</label>
      <input
        v-model="store.apiUrl"
        class="input-text"
        placeholder="https://api.openai.com/v1"
      />
    </div>

    <div class="settings-section">
      <label class="section-label">API Key</label>
      <input
        v-model="store.apiKey"
        class="input-text"
        type="password"
        placeholder="sk-..."
      />
    </div>

    <div class="settings-section">
      <label class="section-label">Model</label>
      <ModelSelector />
    </div>

    <div class="settings-section">
      <label class="section-label">response_format</label>
      <ResponseFormatInput />
    </div>
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { useSettingsStore } from "@/stores/settings";
import PresetSelector from "@/components/PresetSelector.vue";
import ModelSelector from "@/components/ModelSelector.vue";
import ResponseFormatInput from "@/components/ResponseFormatInput.vue";

const store = useSettingsStore();

onMounted(() => {
  store.loadPresets();
});
</script>

<style scoped>
.settings-page {
  max-width: 600px;
  padding: 32px 40px;
  overflow-y: auto;
  height: 100%;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: #333;
  margin-bottom: 28px;
}

.settings-section {
  margin-bottom: 20px;
}

.section-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #888;
  margin-bottom: 6px;
}

.input-text {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d5d5d5;
  border-radius: 8px;
  font-size: 14px;
  color: #333;
  outline: none;
  font-family: inherit;
}
.input-text:focus {
  border-color: #aaa;
}
.input-text::placeholder {
  color: #bbb;
}
</style>
```

- [ ] **Step 2: 创建 PresetSelector.vue**

`frontend/src/components/PresetSelector.vue`：

```vue
<template>
  <div class="preset-row">
    <select v-model="store.activePresetId" class="preset-select" @change="onSelect">
      <option v-for="p in store.presets" :key="p.id" :value="p.id">
        {{ p.name }}
      </option>
    </select>
    <button class="preset-btn" @click="handleNew">新建</button>
    <button class="preset-btn" @click="handleDelete" :disabled="!store.activePresetId">删除</button>
    <button class="preset-btn" @click="handleSave" :disabled="!store.activePresetId">保存</button>
  </div>
</template>

<script setup>
import { useSettingsStore } from "@/stores/settings";
const store = useSettingsStore();

function onSelect() {
  store.selectPreset(store.activePresetId);
}

async function handleNew() {
  const name = prompt("预设名称");
  if (name && name.trim()) {
    await store.createPreset(name.trim());
  }
}

async function handleDelete() {
  if (confirm("确认删除当前预设？")) {
    await store.deletePreset(store.activePresetId);
  }
}

async function handleSave() {
  await store.savePreset();
  alert("保存成功");
}
</script>

<style scoped>
.preset-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.preset-select {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d5d5d5;
  border-radius: 8px;
  font-size: 14px;
  color: #333;
  background: #fff;
  outline: none;
  font-family: inherit;
}

.preset-btn {
  padding: 6px 12px;
  border: 1px solid #d5d5d5;
  border-radius: 6px;
  background: #fff;
  color: #555;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
}
.preset-btn:hover:not(:disabled) {
  background: #f0f0f0;
}
.preset-btn:disabled {
  opacity: 0.4;
  cursor: default;
}
</style>
```

- [ ] **Step 3: 创建 ModelSelector.vue**

`frontend/src/components/ModelSelector.vue`：

```vue
<template>
  <div class="model-row">
    <select v-model="store.model" class="model-select">
      <option v-for="m in store.availableModels" :key="m" :value="m">
        {{ m }}
      </option>
      <option v-if="store.availableModels.length === 0" :value="store.model">
        {{ store.model || 'gpt-4o' }}
      </option>
    </select>
    <button class="fetch-btn" @click="handleFetch" :disabled="fetching">
      {{ fetching ? '...' : '🔄 拉取' }}
    </button>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useSettingsStore } from "@/stores/settings";
const store = useSettingsStore();
const fetching = ref(false);

async function handleFetch() {
  fetching.value = true;
  try {
    await store.fetchModels();
  } catch (e) {
    alert("拉取失败: " + e.message);
  } finally {
    fetching.value = false;
  }
}
</script>

<style scoped>
.model-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.model-select {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d5d5d5;
  border-radius: 8px;
  font-size: 14px;
  color: #333;
  background: #fff;
  outline: none;
  font-family: inherit;
}

.fetch-btn {
  padding: 8px 12px;
  border: 1px solid #d5d5d5;
  border-radius: 6px;
  background: #fff;
  color: #555;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
}
.fetch-btn:hover:not(:disabled) {
  background: #f0f0f0;
}
.fetch-btn:disabled {
  opacity: 0.4;
  cursor: default;
}
</style>
```

- [ ] **Step 4: 创建 ResponseFormatInput.vue**

`frontend/src/components/ResponseFormatInput.vue`：

```vue
<template>
  <textarea
    v-model="store.responseFormat"
    class="resp-format-input"
    placeholder='{"type": "json_object"}'
  ></textarea>
</template>

<script setup>
import { useSettingsStore } from "@/stores/settings";
const store = useSettingsStore();
</script>

<style scoped>
.resp-format-input {
  width: 100%;
  height: 150px;
  padding: 12px;
  border: 1px solid #d5d5d5;
  border-radius: 8px;
  font-size: 13px;
  font-family: "SF Mono", "Fira Code", "Consolas", monospace;
  color: #333;
  outline: none;
  resize: vertical;
  line-height: 1.5;
}
.resp-format-input:focus {
  border-color: #aaa;
}
.resp-format-input::placeholder {
  color: #bbb;
}
</style>
```

- [ ] **Step 5: 启动预览验证**

```bash
cd frontend && npm run dev
```

验证要点：
- 点击左侧 Sidebar "设置"，进入 `/settings`
- 预设下拉可用，可新建/删除/保存
- API URL、API Key 可输入
- Model 下拉 + 🔄 拉取按钮可见
- response_format 大输入区可见

> ⏸️ **检查点 2：用户预览确认设置页后，继续 Task 3。**

---

### Task 3: 对话页 — 消息气泡 + SSE 集成

> 此 Task 将前两个 Task 的组件全部连通，实现完整的对话流程预览。

**Files:**
- Modify: `frontend/src/components/MessageList.vue` (完善 MessageActions 事件绑定)
- Modify: `frontend/src/components/MessageActions.vue` (完善编辑功能)
- No new files

**Interfaces:**
- Consumes: `useChatStore` (所有 actions)、`MessageBubble`、`InputBar`、`WelcomeBanner`
- Produces: 完整的对话页 — 新建对话、发送消息、流式显示、停止、编辑、重放、版本切换

- [ ] **Step 1: 完善 MessageList.vue — 绑定 MessageActions 事件**

`frontend/src/components/MessageList.vue` — 替换 `<MessageActions>` 部分：

找到：
```vue
      <MessageActions
        v-if="isLastAssistant(msg)"
        :message="msg"
      />
```

替换为：
```vue
      <MessageActions
        v-if="isLastAssistant(msg)"
        :message="msg"
        @edit="handleEdit"
        @replay="handleReplay"
        @prev="(id) => chatStore.switchVersion(id, -1)"
        @next="(id) => chatStore.switchVersion(id, 1)"
      />
```

并在 `<script setup>` 中添加：

```js
function handleEdit(id) {
  const msg = chatStore.messages.find((m) => m.id === id);
  if (!msg) return;
  const newContent = prompt("编辑消息", msg.content);
  if (newContent !== null && newContent.trim()) {
    chatStore.editMessage(id, newContent.trim());
  }
}

function handleReplay(id) {
  chatStore.replayMessage(id);
}
```

- [ ] **Step 2: 确认 SSE.js 路径兼容**

`frontend/src/api/sse.js` 中的 fetch URL 前缀是硬编码 `/api`，确认逻辑正确（无需修改，`/api` + url 已经拼接正确）。

- [ ] **Step 3: 启动完整预览**

```bash
cd frontend && npm run dev
```

验证要点：
- 点击"开始新对话" → 进入对话视图，输入栏可见
- 输入消息回车 → 用户气泡出现在右侧
- （需要后端运行）AI 回复气泡出现在左侧，流式逐字显示
- 发送按钮在流式中显示 ⏸，可点击停止
- AI 最后一条消息下方出现 [✎] [🔄] [←] [→] 按钮

> ⏸️ **检查点 3：用户预览确认完整对话流程后，前端 MVP 完成。**

---

## 预览依赖说明

由于后端 API 尚未全部实现，预览时可能遇到：
- 对话列表加载失败（后端 `/api/conversations` 未实现）— 不影响 UI 骨架预览
- SSE 流式无法展示（后端 `/chat` 未实现）— 消息发送按钮逻辑可验证

如需最小可用的后端支持，可临时实现 `/api/conversations` GET + POST 和 `/api/settings` GET 返回空数组即可验证完整流程。
