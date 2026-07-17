# AI Chat 桌面应用前端骨架 · 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个 Electron + Vue 3 的 Windows 桌面聊天应用前端 UI 骨架，包含标题栏、侧边栏、聊天区和输入区的完整交互式布局。

**Architecture:** electron-vite 统一管理 Electron 主进程和 Vue 渲染进程构建；Vue 3 Composition API + Pinia 状态管理 + Tailwind CSS 样式；手写全部组件，遵循 docs/UI_token.md 设计规范。

**Tech Stack:** electron-vite, Vue 3 (Composition API + `<script setup>`), TypeScript, Pinia, Tailwind CSS 3, electron-builder

## Global Constraints

- 亮色主题为默认，暗色主题仅预留 CSS 变量
- 纯前端交互，不涉及后端通信、消息持久化、用户认证
- 手写组件，不依赖 UI 组件库（Element Plus / Naive UI 等）
- 所有样式必须引用 UI_token.md 中的 Token 值
- TypeScript 全程类型安全，禁止 `any`
- 自定义标题栏替代 Windows 原生标题栏
- 输入框点击「发送」仅清空，不产生消息
- 打包目标：Windows .exe

---

### Task 1: 项目脚手架搭建

**Files:**
- Create: `package.json`
- Create: `vite.config.ts`
- Create: `tsconfig.json`
- Create: `tsconfig.node.json`
- Create: `tsconfig.web.json`
- Create: `tailwind.config.js`
- Create: `postcss.config.js`
- Create: `electron-builder.yml`
- Create: `src/main.ts`
- Create: `src/App.vue`（最小占位）
- Create: `src/env.d.ts`
- Create: `index.html`

**Interfaces:**
- Produces: `npm run dev` 可启动 Electron 空白窗口

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "ai-chat",
  "version": "1.0.0",
  "description": "AI Chat Desktop Application",
  "main": "./out/main/index.js",
  "scripts": {
    "dev": "electron-vite dev",
    "build": "electron-vite build && electron-builder",
    "preview": "electron-vite preview"
  },
  "dependencies": {
    "pinia": "^2.1.7",
    "vue": "^3.4.21"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.4",
    "autoprefixer": "^10.4.19",
    "electron": "^30.0.1",
    "electron-builder": "^24.13.3",
    "electron-vite": "^2.1.0",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.3",
    "typescript": "^5.4.5",
    "vite": "^5.2.8",
    "vue-tsc": "^2.0.11"
  }
}
```

- [ ] **Step 2: 安装依赖**

```bash
npm install
```

- [ ] **Step 3: 创建 electron-vite 配置文件**

`electron.vite.config.ts`:
```typescript
import { resolve } from 'path'
import { defineConfig, externalizeDepsPlugin } from 'electron-vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin()],
  },
  preload: {
    plugins: [externalizeDepsPlugin()],
  },
  renderer: {
    resolve: {
      alias: {
        '@': resolve('src'),
      },
    },
    plugins: [vue()],
  },
})
```

- [ ] **Step 4: 创建 tsconfig 文件**

`tsconfig.json`:
```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.node.json" },
    { "path": "./tsconfig.web.json" }
  ]
}
```

`tsconfig.node.json`:
```json
{
  "compilerOptions": {
    "composite": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "allowSyntheticDefaultImports": true,
    "esModuleInterop": true,
    "outDir": "./out",
    "declaration": true,
    "strict": true,
    "skipLibCheck": true,
    "target": "ESNext"
  },
  "include": [
    "electron/**/*.ts",
    "electron.vite.config.ts"
  ]
}
```

`tsconfig.web.json`:
```json
{
  "compilerOptions": {
    "composite": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true,
    "esModuleInterop": true,
    "jsx": "preserve",
    "outDir": "./out",
    "declaration": true,
    "strict": true,
    "skipLibCheck": true,
    "target": "ESNext",
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": [
    "src/**/*.ts",
    "src/**/*.d.ts",
    "src/**/*.vue"
  ]
}
```

- [ ] **Step 5: 创建 Tailwind + PostCSS 配置**

`tailwind.config.js`:
```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{vue,ts,html}'],
  theme: {
    extend: {
      colors: {
        accent: '#6366f1',
        'accent-hover': '#4f46e5',
        sidebar: '#f8fafc',
        chat: '#ffffff',
        danger: '#f87171',
        'danger-hover': '#ef4444',
      },
      spacing: {
        titlebar: '36px',
        sidebar: '260px',
      },
      borderRadius: {
        bubble: '14px',
      },
      fontSize: {
        xs: '12px',
        sm: '13px',
        base: '14px',
        md: '15px',
        lg: '18px',
        xl: '24px',
      },
    },
  },
  plugins: [],
}
```

`postcss.config.js`:
```js
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 6: 创建入口 HTML 和 Vue 入口**

`index.html`:
```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AI Chat</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

`src/main.ts`:
```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './assets/styles/main.css'

const app = createApp(App)
app.use(createPinia())
app.mount('#app')
```

`src/App.vue`:
```vue
<template>
  <div class="w-screen h-screen bg-white text-slate-800 flex items-center justify-center">
    <p class="text-xl font-semibold">AI Chat — 加载中...</p>
  </div>
</template>
```

`src/env.d.ts`:
```typescript
/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}
```

- [ ] **Step 7: 创建 electron-builder.yml**

```yaml
appId: com.aichat.desktop
productName: AI Chat
directories:
  output: dist
win:
  target: nsis
  icon: null
nsis:
  oneClick: false
  allowToChangeInstallationDirectory: true
```

- [ ] **Step 8: 创建 Electron 主进程最小文件**

`electron/main.ts`:
```typescript
import { app, BrowserWindow, shell } from 'electron'
import { join } from 'path'
import { is } from '@electron-toolkit/utils'

function createWindow(): void {
  const mainWindow = new BrowserWindow({
    width: 1100,
    height: 750,
    minWidth: 800,
    minHeight: 500,
    show: false,
    frame: false,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
    },
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(() => {
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
```

`electron/preload.ts`:
```typescript
import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  minimize: () => ipcRenderer.send('window:minimize'),
  maximize: () => ipcRenderer.send('window:maximize'),
  close: () => ipcRenderer.send('window:close'),
})
```

- [ ] **Step 9: 安装 electron 工具包依赖 & 验证**

```bash
npm install --save-dev @electron-toolkit/utils
npm run dev
```

预期：Electron 窗口启动，显示 "AI Chat — 加载中..."

- [ ] **Step 10: 提交**

```bash
git add .
git commit -m "feat: scaffold project with electron-vite + Vue 3 + Tailwind + Pinia"
```

---

### Task 2: 类型定义 & 全局样式

**Files:**
- Create: `src/types/index.ts`
- Create: `src/assets/styles/main.css`
- Create: `src/assets/styles/theme.css`

**Interfaces:**
- Produces: `Session` 接口, `AppState` 接口, CSS 变量定义, Tailwind 基础样式

- [ ] **Step 1: 创建类型定义**

`src/types/index.ts`:
```typescript
export interface Session {
  id: string
  title: string
  createdAt: number
}

export interface AppState {
  sidebarCollapsed: boolean
  currentSessionId: string | null
  theme: 'dark' | 'light'
}
```

- [ ] **Step 2: 创建 CSS 变量主题文件**

`src/assets/styles/theme.css`:
```css
:root {
  /* 背景 */
  --bg-app: #ffffff;
  --bg-sidebar: #f8fafc;
  --bg-chat: #ffffff;
  --bg-input: #f8fafc;
  --bg-hover: #f1f5f9;
  --bg-active: #6366f1;

  /* 文字 */
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-tertiary: #94a3b8;
  --text-inverse: #ffffff;
  --text-danger: #f87171;

  /* 边框 */
  --border-light: #e2e8f0;
  --border-default: #e2e8f0;
  --border-focus: #6366f1;

  /* 强调 */
  --accent: #6366f1;
  --accent-hover: #4f46e5;
  --accent-light: #818cf8;
  --danger: #f87171;
  --danger-hover: #ef4444;

  /* 圆角 */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-full: 9999px;

  /* 阴影 */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);

  /* 过渡 */
  --transition-fast: 150ms ease;
  --transition-base: 200ms ease;
  --transition-slow: 300ms ease;
}

/* 暗色主题预留 */
html.dark {
  --bg-app: #1a1a2e;
  --bg-sidebar: #16213e;
  --bg-chat: #0f0f23;
  --bg-input: #1e293b;
  --bg-hover: #334155;
  --bg-active: #6366f1;

  --text-primary: #e2e8f0;
  --text-secondary: #94a3b8;
  --text-tertiary: #64748b;
  --text-inverse: #ffffff;

  --border-light: #2d2d5e;
  --border-default: #334155;
  --border-focus: #818cf8;

  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
}
```

- [ ] **Step 3: 创建 Tailwind 入口 CSS**

`src/assets/styles/main.css`:
```css
@import './theme.css';

@tailwind base;
@tailwind components;
@tailwind utilities;

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei',
    sans-serif;
  font-size: 14px;
  color: var(--text-primary);
  background: var(--bg-app);
  overflow: hidden;
  user-select: none;
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 4px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--border-light);
  border-radius: 2px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-tertiary);
}
```

- [ ] **Step 4: 验证编译**

```bash
npx vue-tsc --noEmit
```

预期：无类型错误。

- [ ] **Step 5: 提交**

```bash
git add src/types/index.ts src/assets/styles/
git commit -m "feat: add type definitions and global theme CSS variables"
```

---

### Task 3: Pinia 状态管理

**Files:**
- Create: `src/stores/session.ts`
- Create: `src/stores/app.ts`

**Interfaces:**
- Consumes: `Session` from `src/types/index.ts`
- Produces:
  - `useSessionStore()` → `{ sessions, currentId, currentSession, createSession, switchSession, deleteSession }`
  - `useAppStore()` → `{ sidebarCollapsed, theme, toggleSidebar, setTheme }`

- [ ] **Step 1: 创建会话 Store**

`src/stores/session.ts`:
```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Session } from '@/types'

export const useSessionStore = defineStore('session', () => {
  const sessions = ref<Session[]>([])
  const currentId = ref<string | null>(null)

  const currentSession = computed(() =>
    sessions.value.find((s) => s.id === currentId.value) ?? null,
  )

  function createSession(): string {
    const id = crypto.randomUUID()
    const session: Session = {
      id,
      title: '新会话',
      createdAt: Date.now(),
    }
    sessions.value.unshift(session)
    currentId.value = id
    return id
  }

  function switchSession(id: string): void {
    if (sessions.value.some((s) => s.id === id)) {
      currentId.value = id
    }
  }

  function deleteSession(id: string): void {
    const idx = sessions.value.findIndex((s) => s.id === id)
    if (idx === -1) return

    sessions.value.splice(idx, 1)

    if (currentId.value === id) {
      if (sessions.value.length > 0) {
        currentId.value = sessions.value[Math.min(idx, sessions.value.length - 1)].id
      } else {
        currentId.value = null
      }
    }
  }

  return { sessions, currentId, currentSession, createSession, switchSession, deleteSession }
})
```

- [ ] **Step 2: 创建应用 UI Store**

`src/stores/app.ts`:
```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const theme = ref<'dark' | 'light'>('light')

  function toggleSidebar(): void {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setTheme(t: 'dark' | 'light'): void {
    theme.value = t
    document.documentElement.classList.toggle('dark', t === 'dark')
  }

  return { sidebarCollapsed, theme, toggleSidebar, setTheme }
})
```

- [ ] **Step 3: 验证编译**

```bash
npx vue-tsc --noEmit
```

预期：无类型错误。

- [ ] **Step 4: 提交**

```bash
git add src/stores/
git commit -m "feat: add Pinia stores for session and app state"
```

---

### Task 4: AppTitleBar + AppLayout

**Files:**
- Create: `src/components/layout/AppTitleBar.vue`
- Create: `src/components/layout/AppLayout.vue`

**Interfaces:**
- Consumes: `electronAPI.minimize/maximize/close` from preload (via `window.electronAPI`)
- Produces: `AppLayout` 包裹所有子组件（标题栏 + 主体区域）

- [ ] **Step 1: 创建自定义标题栏**

`src/components/layout/AppTitleBar.vue`:
```vue
<template>
  <div
    class="app-titlebar flex items-center justify-between h-titlebar bg-[var(--bg-app)] border-b border-[var(--border-light)]"
    style="-webkit-app-region: drag"
  >
    <span class="pl-4 text-sm font-medium text-[var(--text-secondary)] select-none">
      AI Chat
    </span>
    <div class="flex h-full" style="-webkit-app-region: no-drag">
      <button
        class="w-[46px] h-full flex items-center justify-center text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] transition-fast"
        @click="minimize"
      >
        <svg width="12" height="12" viewBox="0 0 12 12"><rect y="5" width="12" height="1.5" fill="currentColor"/></svg>
      </button>
      <button
        class="w-[46px] h-full flex items-center justify-center text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] transition-fast"
        @click="maximize"
      >
        <svg width="12" height="12" viewBox="0 0 12 12"><rect x="1" y="1" width="10" height="10" stroke="currentColor" stroke-width="1.5" fill="none"/></svg>
      </button>
      <button
        class="w-[46px] h-full flex items-center justify-center text-[var(--text-secondary)] hover:bg-[var(--danger)] hover:text-white transition-fast"
        @click="close"
      >
        <svg width="12" height="12" viewBox="0 0 12 12"><line x1="1" y1="1" x2="11" y2="11" stroke="currentColor" stroke-width="1.5"/><line x1="11" y1="1" x2="1" y2="11" stroke="currentColor" stroke-width="1.5"/></svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
const api = (window as any).electronAPI

function minimize() { api?.minimize() }
function maximize() { api?.maximize() }
function close() { api?.close() }
</script>
```

- [ ] **Step 2: 创建布局容器**

`src/components/layout/AppLayout.vue`:
```vue
<template>
  <div class="w-screen h-screen flex flex-col bg-[var(--bg-app)]">
    <AppTitleBar />
    <div class="flex flex-1 overflow-hidden">
      <slot name="sidebar" />
      <slot name="chat" />
    </div>
  </div>
</template>

<script setup lang="ts">
import AppTitleBar from './AppTitleBar.vue'
</script>
```

- [ ] **Step 3: 验证编译**

```bash
npx vue-tsc --noEmit
```

预期：无类型错误。

- [ ] **Step 4: 提交**

```bash
git add src/components/layout/
git commit -m "feat: add AppTitleBar and AppLayout components"
```

---

### Task 5: 侧边栏组件（Sidebar + SessionList + SessionItem）

**Files:**
- Create: `src/components/sidebar/Sidebar.vue`
- Create: `src/components/sidebar/SessionList.vue`
- Create: `src/components/sidebar/SessionItem.vue`

**Interfaces:**
- Consumes: `useSessionStore()` from `src/stores/session.ts`
- Produces: 可交互的会话侧边栏

- [ ] **Step 1: 创建 SessionItem 组件**

`src/components/sidebar/SessionItem.vue`:
```vue
<template>
  <div
    class="group flex items-center h-[56px] px-4 mx-2 rounded-[var(--radius-md)] cursor-pointer transition-base select-none"
    :class="isActive
      ? 'bg-[var(--bg-active)] text-[var(--text-inverse)]'
      : 'hover:bg-[var(--bg-hover)] text-[var(--text-primary)]'"
    @click="$emit('select')"
  >
    <div class="flex-1 min-w-0">
      <p class="text-[15px] font-medium truncate">{{ session.title }}</p>
      <p
        class="text-xs mt-0.5"
        :class="isActive ? 'text-white/70' : 'text-[var(--text-tertiary)]'"
      >
        {{ formatTime(session.createdAt) }}
      </p>
    </div>
    <button
      class="ml-2 p-1 rounded-[var(--radius-sm)] opacity-0 group-hover:opacity-100 transition-fast"
      :class="isActive
        ? 'hover:bg-white/20 text-white/80'
        : 'hover:bg-[var(--danger)] text-[var(--text-tertiary)] hover:text-white'"
      @click.stop="$emit('delete')"
    >
      <svg width="14" height="14" viewBox="0 0 14 14">
        <line x1="3" y1="3" x2="11" y2="11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        <line x1="11" y1="3" x2="3" y2="11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import type { Session } from '@/types'

defineProps<{
  session: Session
  isActive: boolean
}>()

defineEmits<{
  select: []
  delete: []
}>()

function formatTime(ts: number): string {
  const d = new Date(ts)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  if (isToday) {
    return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>
```

- [ ] **Step 2: 创建 SessionList 组件**

`src/components/sidebar/SessionList.vue`:
```vue
<template>
  <div class="flex-1 overflow-y-auto py-1">
    <SessionItem
      v-for="session in sessions"
      :key="session.id"
      :session="session"
      :isActive="session.id === currentId"
      @select="$emit('select', session.id)"
      @delete="$emit('delete', session.id)"
    />
    <div
      v-if="sessions.length === 0"
      class="px-4 py-8 text-center text-sm text-[var(--text-tertiary)]"
    >
      暂无会话
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Session } from '@/types'
import SessionItem from './SessionItem.vue'

defineProps<{
  sessions: Session[]
  currentId: string | null
}>()

defineEmits<{
  select: [id: string]
  delete: [id: string]
}>()
</script>
```

- [ ] **Step 3: 创建 Sidebar 容器**

`src/components/sidebar/Sidebar.vue`:
```vue
<template>
  <div
    class="w-sidebar flex-shrink-0 flex flex-col bg-[var(--bg-sidebar)] border-r border-[var(--border-light)]"
  >
    <div class="flex items-center justify-between h-12 px-4">
      <span class="text-lg font-semibold text-[var(--text-primary)]">会话</span>
      <button
        class="w-8 h-8 flex items-center justify-center rounded-[var(--radius-sm)] bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)] transition-fast"
        @click="create"
      >
        <svg width="16" height="16" viewBox="0 0 16 16">
          <line x1="8" y1="2" x2="8" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <line x1="2" y1="8" x2="14" y2="8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </button>
    </div>
    <SessionList
      :sessions="store.sessions"
      :currentId="store.currentId"
      @select="store.switchSession"
      @delete="store.deleteSession"
    />
  </div>
</template>

<script setup lang="ts">
import { useSessionStore } from '@/stores/session'
import SessionList from './SessionList.vue'

const store = useSessionStore()

function create() {
  store.createSession()
}
</script>
```

- [ ] **Step 4: 验证编译**

```bash
npx vue-tsc --noEmit
```

预期：无类型错误。

- [ ] **Step 5: 提交**

```bash
git add src/components/sidebar/
git commit -m "feat: add Sidebar, SessionList, and SessionItem components"
```

---

### Task 6: 聊天区组件（ChatView + MessageList + InputArea）

**Files:**
- Create: `src/components/chat/ChatView.vue`
- Create: `src/components/chat/MessageList.vue`
- Create: `src/components/chat/InputArea.vue`

**Interfaces:**
- Consumes: `useSessionStore()` from `src/stores/session.ts`
- Produces: 聊天区界面（头部 + 占位欢迎 + 输入框）

- [ ] **Step 1: 创建 MessageList（占位）**

`src/components/chat/MessageList.vue`:
```vue
<template>
  <div class="flex-1 overflow-y-auto flex flex-col items-center justify-center p-6">
    <div class="text-center">
      <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-[var(--bg-hover)] flex items-center justify-center">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" stroke-width="1.5" stroke-linecap="round">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/>
          <circle cx="8" cy="10" r="1" fill="var(--text-tertiary)" stroke="none"/>
          <circle cx="16" cy="10" r="1" fill="var(--text-tertiary)" stroke="none"/>
          <path d="M8 15c1.5 2 4 2 8 0"/>
        </svg>
      </div>
      <h2 class="text-[24px] font-semibold text-[var(--text-primary)] mb-2">
        欢迎使用 AI Chat
      </h2>
      <p class="text-sm text-[var(--text-tertiary)]">
        选择一个会话或创建新会话开始对话
      </p>
    </div>
  </div>
</template>
```

- [ ] **Step 2: 创建 InputArea**

`src/components/chat/InputArea.vue`:
```vue
<template>
  <div class="border-t border-[var(--border-light)] bg-white px-6 py-4">
    <div class="flex items-end gap-3 max-w-3xl mx-auto">
      <textarea
        v-model="text"
        class="flex-1 resize-none rounded-[var(--radius-md)] border border-[var(--border-light)] bg-[var(--bg-input)] px-4 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] outline-none transition-base focus:border-[var(--border-focus)] focus:shadow-[var(--shadow-sm)]"
        rows="1"
        placeholder="输入消息..."
        @keydown.enter.exact.prevent="send"
      />
      <button
        class="flex-shrink-0 px-5 py-2.5 rounded-[var(--radius-sm)] text-sm font-semibold text-white transition-base"
        :class="text.trim()
          ? 'bg-[var(--accent)] hover:bg-[var(--accent-hover)] cursor-pointer'
          : 'bg-[var(--text-tertiary)] cursor-not-allowed'"
        :disabled="!text.trim()"
        @click="send"
      >
        发送
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const text = ref('')

function send(): void {
  if (!text.value.trim()) return
  text.value = ''
}
</script>
```

- [ ] **Step 3: 创建 ChatView 容器**

`src/components/chat/ChatView.vue`:
```vue
<template>
  <div class="flex-1 flex flex-col bg-[var(--bg-chat)] min-w-0">
    <div
      v-if="store.currentSession"
      class="flex items-center h-12 px-6 border-b border-[var(--border-light)] flex-shrink-0"
    >
      <span class="text-[15px] font-medium text-[var(--text-primary)] truncate">
        {{ store.currentSession.title }}
      </span>
    </div>
    <MessageList />
    <InputArea />
  </div>
</template>

<script setup lang="ts">
import { useSessionStore } from '@/stores/session'
import MessageList from './MessageList.vue'
import InputArea from './InputArea.vue'

const store = useSessionStore()
</script>
```

- [ ] **Step 4: 验证编译**

```bash
npx vue-tsc --noEmit
```

预期：无类型错误。

- [ ] **Step 5: 提交**

```bash
git add src/components/chat/
git commit -m "feat: add ChatView, MessageList, and InputArea components"
```

---

### Task 7: App.vue 总装 & 窗口控制 IPC

**Files:**
- Modify: `src/App.vue`
- Modify: `electron/main.ts`（添加窗口控制 IPC）

**Interfaces:**
- Consumes: `AppLayout`, `Sidebar`, `ChatView`, `useSessionStore`
- Produces: 完整可运行的应用

- [ ] **Step 1: 更新 App.vue**

`src/App.vue`:
```vue
<template>
  <AppLayout>
    <template #sidebar>
      <Sidebar />
    </template>
    <template #chat>
      <ChatView />
    </template>
  </AppLayout>
</template>

<script setup lang="ts">
import AppLayout from './components/layout/AppLayout.vue'
import Sidebar from './components/sidebar/Sidebar.vue'
import ChatView from './components/chat/ChatView.vue'
</script>
```

- [ ] **Step 2: 在主进程添加窗口控制 IPC**

在 `electron/main.ts` 的 `createWindow` 函数中，`mainWindow` 声明之后添加：

```typescript
import { ipcMain } from 'electron'

// ... 在 createWindow 函数内, mainWindow 定义之后:
  ipcMain.on('window:minimize', () => mainWindow.minimize())
  ipcMain.on('window:maximize', () => {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize()
    } else {
      mainWindow.maximize()
    }
  })
  ipcMain.on('window:close', () => mainWindow.close())
```

需要把 `ipcMain` 导入加到文件顶部：

```typescript
import { app, BrowserWindow, shell, ipcMain } from 'electron'
```

完整 `electron/main.ts`:
```typescript
import { app, BrowserWindow, shell, ipcMain } from 'electron'
import { join } from 'path'
import { is } from '@electron-toolkit/utils'

function createWindow(): void {
  const mainWindow = new BrowserWindow({
    width: 1100,
    height: 750,
    minWidth: 800,
    minHeight: 500,
    show: false,
    frame: false,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
    },
  })

  ipcMain.on('window:minimize', () => mainWindow.minimize())
  ipcMain.on('window:maximize', () => {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize()
    } else {
      mainWindow.maximize()
    }
  })
  ipcMain.on('window:close', () => mainWindow.close())

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(() => {
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
```

- [ ] **Step 3: 启动验证**

```bash
npm run dev
```

预期：
1. Electron 窗口无原生标题栏，自定义标题栏正常显示
2. 左侧 260px 侧边栏，右侧聊天区
3. 点击标题栏按钮可最小化/最大化/关闭
4. 点击「+」按钮新增会话，自动切换
5. 点击会话项切换高亮
6. 悬停会话项显示删除按钮，点击可删除
7. 输入框可输入文字，点击「发送」清空

- [ ] **Step 4: 提交**

```bash
git add src/App.vue electron/main.ts
git commit -m "feat: wire up App.vue with full layout and window control IPC"
```

---

### Task 8: 打包验证

**Files:**
- No new files

**Interfaces:**
- Produces: `npm run build` 输出 Windows .exe

- [ ] **Step 1: 执行构建**

```bash
npm run build
```

预期：`dist/` 目录下生成 Windows 安装包（.exe）。

- [ ] **Step 2: 最终提交**

```bash
git add .
git commit -m "chore: finalize build configuration"
```

---

## 验收检查清单

| # | 标准 | 对应 Task |
|---|---|---|
| 1 | `npm run dev` 启动 Electron 窗口，显示完整三栏布局 | Task 7 |
| 2 | 自定义标题栏可拖拽、可最小化/最大化/关闭 | Task 4+7 |
| 3 | 点击「新建」侧边栏新增会话，自动切换 | Task 5 |
| 4 | 点击会话项可切换，高亮正确 | Task 5 |
| 5 | 可删除会话（删除当前会话时自动切换到其他会话） | Task 5 |
| 6 | 输入框可输入，点击发送清空 | Task 6 |
| 7 | `npm run build` 输出 Windows .exe | Task 8 |
