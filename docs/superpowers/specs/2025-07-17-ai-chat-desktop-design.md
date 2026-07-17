# AI Chat — Windows 桌面聊天应用前端骨架 · 设计规格

> 日期：2025-07-17 | 状态：已批准 | 版本：1.0

## 1. 项目概述

构建一个 **Windows 桌面 AI 聊天应用的前端 UI 骨架**，具备完整的布局、会话管理交互和可扩展的架构。本阶段仅实现纯前端交互，不涉及 AI 对话逻辑、后端通信和消息数据持久化。

## 2. 技术栈

| 层 | 选型 | 说明 |
|---|---|---|
| 桌面壳 | Electron | Windows 原生窗口 + 系统托盘/通知能力 |
| 前端框架 | Vue 3 | Composition API + `<script setup>` |
| 构建工具 | electron-vite | 统一管理主进程 & 渲染进程的 Vite 构建 |
| 状态管理 | Pinia | Vue 3 官方推荐，TypeScript 友好 |
| 样式 | Tailwind CSS 3 + CSS 变量 | 手写组件，不依赖 UI 组件库；设计 Token 见 docs/UI_token.md |
| 类型 | TypeScript | 全程类型安全 |
| 打包 | electron-builder | 输出 Windows .exe 安装包 |

## 3. 目录结构

```
chat/
├── electron/                    # Electron 主进程
│   ├── main.ts                  # 入口：创建窗口、生命周期
│   └── preload.ts               # 预加载脚本（安全暴露 IPC）
├── src/                         # Vue 前端（渲染进程）
│   ├── main.ts                  # Vue 入口
│   ├── App.vue                  # 根组件
│   ├── assets/
│   │   └── styles/
│   │       ├── main.css         # Tailwind 指令 + CSS 变量
│   │       └── theme.css        # 暗色/亮色主题变量
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppTitleBar.vue  # 自定义标题栏（最小化/最大化/关闭）
│   │   │   └── AppLayout.vue    # 三栏布局容器
│   │   ├── sidebar/
│   │   │   ├── Sidebar.vue      # 侧边栏容器
│   │   │   ├── SessionList.vue  # 会话列表
│   │   │   └── SessionItem.vue  # 单个会话项
│   │   └── chat/
│   │       ├── ChatView.vue     # 聊天区容器
│   │       ├── MessageList.vue  # 消息列表（占位）
│   │       └── InputArea.vue    # 输入区域
│   ├── stores/
│   │   ├── session.ts           # 会话状态（Pinia）
│   │   └── app.ts               # 全局 UI 状态
│   └── types/
│       └── index.ts             # TypeScript 类型定义
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── electron-builder.yml         # Windows 打包配置
```

## 4. 组件树 & 布局

```
App.vue
└── AppLayout.vue                    # CSS Grid 三栏：标题栏 | 侧边栏+聊天区
    ├── AppTitleBar.vue              # 顶部 36px，拖拽区域 + 窗口控制按钮
    └── [main-area]                  # flex-row，占据剩余空间
        ├── Sidebar.vue              # 左侧 260px，flex-col
        │   ├── [header]             #   "会话" 标题 + 新建按钮
        │   └── SessionList.vue       #   可滚动会话列表
        │       └── SessionItem.vue   #   头像 + 标题 + 时间，支持 active/删除
        └── ChatView.vue             # 右侧 flex-1，flex-col
            ├── [header]             #   当前会话标题
            ├── MessageList.vue      #   flex-1 可滚动区域（占位欢迎语）
            └── InputArea.vue        #   底部固定，textarea + 发送按钮
```

**布局示意：**

```
┌──────────────────────────────────────────┐
│  AppTitleBar          ╴  ─  ✕           │ 36px
├────────────┬─────────────────────────────┤
│  Sidebar   │  ChatView                   │
│  260px     │                             │
│            │  "欢迎使用 AI Chat"          │
│  ┌──────┐  │                             │
│  │ 新建  │  │  MessageList (flex-1)       │
│  ├──────┤  │                             │
│  │ 会话1 │  │                             │
│  │ 会话2 │  ├─────────────────────────────┤
│  │ 会话3 │  │  InputArea                  │
│  │      │  │  [________________] [发送]  │
│  └──────┘  └─────────────────────────────┘
└──────────────────────────────────────────┘
```

## 5. 交互行为

| 操作 | 行为 |
|---|---|
| 点击「新建」按钮 | 侧边栏新增一个会话项，自动切换到新会话 |
| 点击会话项 | 高亮切换，ChatView 显示对应会话的占位内容 |
| 右键/悬停会话项 | 显示删除按钮，点击删除会话 |
| 输入框输入文字 | 可正常输入 |
| 点击「发送」 | 清空输入框（不产生消息、不调用后端） |

**不实现：** 消息渲染、消息历史、后端通信、Markdown 渲染、文件上传、用户认证。

## 6. 状态管理

```typescript
// types/index.ts
interface Session {
  id: string;          // crypto.randomUUID()
  title: string;       // 默认 "新会话"
  createdAt: number;   // Date.now()
}

interface AppState {
  sidebarCollapsed: boolean;
  currentSessionId: string | null;
  theme: 'dark' | 'light';
}
```

| Store | State | Actions |
|---|---|---|
| `useSessionStore` | `sessions: Session[]`<br>`currentId: string \| null` | `createSession()`<br>`switchSession(id)`<br>`deleteSession(id)` |
| `useAppStore` | `sidebarCollapsed: boolean`<br>`theme: string` | `toggleSidebar()`<br>`setTheme(t)` |

## 7. 样式 & 主题

**亮色主题（默认）：** 设计 Token 详见 `docs/UI_token.md`，此处为概要。

| 变量 | 值 | 用途 |
|---|---|---|
| `--bg-primary` | `#ffffff` | 主背景 |
| `--bg-sidebar` | `#f8fafc` | 侧边栏背景 |
| `--bg-chat` | `#ffffff` | 聊天区背景 |
| `--accent` | `#6366f1` | 按钮/高亮靛蓝 |
| `--accent-hover` | `#4f46e5` | 悬停加深 |
| `--text-primary` | `#1e293b` | 主文字 |
| `--text-secondary` | `#64748b` | 次要文字 |
| `--border` | `#e2e8f0` | 边框/分割线 |
| `--radius-sm` | `6px` | 小圆角 |
| `--radius-md` | `10px` | 中圆角 |
| `--radius-lg` | `14px` | 大圆角 |
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | 微阴影 |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.07)` | 中阴影 |

CSS 变量统一在 `docs/UI_token.md` 中定义，`src/assets/styles/theme.css` 中引用实现。默认亮色主题，暗色主题预留。

## 8. 非目标（明确排除）

- ❌ 后端通信（HTTP/WebSocket）
- ❌ AI 对话逻辑
- ❌ 消息持久化（LocalStorage/数据库）
- ❌ 用户认证
- ❌ Markdown/代码高亮渲染
- ❌ 文件/图片上传
- ❌ 暗色主题切换（仅预留变量）
- ❌ 多窗口

## 9. 验收标准

1. `npm run dev` 启动 Electron 窗口，显示完整三栏布局
2. 自定义标题栏可拖拽、可最小化/最大化/关闭
3. 点击「新建」侧边栏新增会话，自动切换
4. 点击会话项可切换，高亮正确
5. 可删除会话（删除当前会话时自动切换到其他会话）
6. 输入框可输入，点击发送清空
7. `npm run build` 输出 Windows .exe
