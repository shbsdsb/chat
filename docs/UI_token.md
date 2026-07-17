# UI Token — AI Chat 全局设计规范

> 版本：1.0 | 最后更新：2025-07-17

本文档定义 AI Chat 桌面应用的全局设计 Token，所有视觉实现以此为准。Token 分为三层：**原始 Token**（色板、字号、间距）→ **语义 Token**（按用途命名）→ **组件 Token**（按组件分配）。

---

## 1. 原始 Token（Primitives）

### 1.1 色板

| Token | 值 | 说明 |
|---|---|---|
| `white` | `#ffffff` | 纯白 |
| `slate-50` | `#f8fafc` | 极浅灰（侧边栏背景） |
| `slate-100` | `#f1f5f9` | 浅灰（卡片悬浮） |
| `slate-200` | `#e2e8f0` | 边框灰 |
| `slate-300` | `#cbd5e1` | 分割线 |
| `slate-400` | `#94a3b8` | 占位文字/禁用态 |
| `slate-500` | `#64748b` | 次要文字 |
| `slate-600` | `#475569` | 辅助文字 |
| `slate-700` | `#334155` | 正文 |
| `slate-800` | `#1e293b` | 主文字/标题 |
| `slate-900` | `#0f172a` | 强调文字 |
| `indigo-400` | `#818cf8` | 轻强调 |
| `indigo-500` | `#6366f1` | 主强调色 |
| `indigo-600` | `#4f46e5` | 悬停/按下 |
| `red-400` | `#f87171` | 危险/删除 |
| `red-500` | `#ef4444` | 危险悬停 |

### 1.2 字号 & 字重

| Token | 值 | 说明 |
|---|---|---|
| `font-xs` | `12px` | 标签/时间戳 |
| `font-sm` | `13px` | 次要文案 |
| `font-base` | `14px` | 正文/默认 |
| `font-md` | `15px` | 会话标题 |
| `font-lg` | `18px` | 区域标题 |
| `font-xl` | `24px` | 欢迎标题 |
| `font-weight-normal` | `400` | 正文 |
| `font-weight-medium` | `500` | 强调 |
| `font-weight-semibold` | `600` | 标题/按钮 |

### 1.3 间距

| Token | 值 | 说明 |
|---|---|---|
| `space-xs` | `4px` | 紧凑内边距 |
| `space-sm` | `8px` | 元素内间距 |
| `space-md` | `12px` | 列表项间距 |
| `space-lg` | `16px` | 组件间距 |
| `space-xl` | `20px` | 区块间距 |
| `space-2xl` | `24px` | 页面边距 |

### 1.4 圆角

| Token | 值 | 说明 |
|---|---|---|
| `radius-sm` | `6px` | 按钮/输入框 |
| `radius-md` | `10px` | 卡片/会话项 |
| `radius-lg` | `14px` | 消息气泡 |
| `radius-full` | `9999px` | 圆形头像 |

### 1.5 阴影

| Token | 值 | 说明 |
|---|---|---|
| `shadow-none` | `none` | 无阴影 |
| `shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | 输入框/卡片默认 |
| `shadow-md` | `0 4px 12px rgba(0,0,0,0.08)` | 悬浮/弹窗 |

### 1.6 过渡

| Token | 值 | 说明 |
|---|---|---|
| `transition-fast` | `150ms ease` | 按钮悬停/点击 |
| `transition-base` | `200ms ease` | 通用过渡 |
| `transition-slow` | `300ms ease` | 面板展开/切换 |

---

## 2. 语义 Token（Semantic）

语义 Token 将原始值绑定到具体用途，上层组件只引用语义 Token。

### 2.1 背景

| Token | 值 | 用途 |
|---|---|---|
| `--bg-app` | `white` | 应用最外层背景 |
| `--bg-sidebar` | `slate-50` | 侧边栏底色 |
| `--bg-chat` | `white` | 聊天区底色 |
| `--bg-input` | `slate-50` | 输入框背景 |
| `--bg-hover` | `slate-100` | 列表项悬停 |
| `--bg-active` | `indigo-500` | 列表项选中 |

### 2.2 文字

| Token | 值 | 用途 |
|---|---|---|
| `--text-primary` | `slate-800` | 主文字：标题、正文 |
| `--text-secondary` | `slate-500` | 次要文字：时间、摘要 |
| `--text-tertiary` | `slate-400` | 辅助文字：占位符 |
| `--text-inverse` | `white` | 反色文字：选中项/按钮 |
| `--text-danger` | `red-400` | 危险操作文字 |

### 2.3 边框 & 分割

| Token | 值 | 用途 |
|---|---|---|
| `--border-light` | `slate-200` | 卡片/输入框边框 |
| `--border-default` | `slate-200` | 列表分割线 |
| `--border-focus` | `indigo-500` | 输入框聚焦边框 |

### 2.4 强调色

| Token | 值 | 用途 |
|---|---|---|
| `--accent` | `indigo-500` | 主按钮/链接/选中态 |
| `--accent-hover` | `indigo-600` | 主按钮悬停 |
| `--accent-light` | `indigo-400` | 轻强调（badge/图标） |
| `--danger` | `red-400` | 删除按钮 |
| `--danger-hover` | `red-500` | 删除按钮悬停 |

---

## 3. 组件 Token

### 3.1 AppTitleBar

| 属性 | Token |
|---|---|
| 高度 | `36px` |
| 背景 | `--bg-app` |
| 底部边框 | `1px solid --border-light` |
| 按钮区域 | 右侧 120px |
| 按钮尺寸 | `36×36px` |
| 按钮悬停 | `--bg-hover` |
| 关闭按钮悬停 | `--danger` |

### 3.2 Sidebar

| 属性 | Token |
|---|---|
| 宽度 | `260px` |
| 背景 | `--bg-sidebar` |
| 右边框 | `1px solid --border-light` |
| 头部内边距 | `space-lg` |
| 头部高度 | `48px` |

### 3.3 SessionItem

| 属性 | Token |
|---|---|
| 高度 | `56px` |
| 内边距 | `space-md space-lg` |
| 圆角 | `radius-md` |
| 默认背景 | 透明 |
| 悬停背景 | `--bg-hover` |
| 选中背景 | `--bg-active` |
| 选中文字 | `--text-inverse` |
| 标题字号 | `font-md` / `font-weight-medium` |
| 时间字号 | `font-xs` / `--text-tertiary` |
| 删除按钮颜色 | `--danger` |

### 3.4 ChatView

| 属性 | Token |
|---|---|
| 背景 | `--bg-chat` |
| 头部高度 | `48px` |
| 头部边框 | `1px solid --border-light` |
| 欢迎图标/标题 | `--text-tertiary` |

### 3.5 MessageList

| 属性 | Token |
|---|---|
| 内边距 | `space-2xl` |
| 占位文字颜色 | `--text-tertiary` |
| 占位文字字号 | `font-base` |

### 3.6 InputArea

| 属性 | Token |
|---|---|
| 容器背景 | `white` |
| 顶部边框 | `1px solid --border-light` |
| 内边距 | `space-lg space-2xl` |
| 输入框背景 | `--bg-input` |
| 输入框圆角 | `radius-md` |
| 输入框聚焦边框 | `--border-focus` |
| 输入框字号 | `font-base` |
| 发送按钮背景 | `--accent` |
| 发送按钮悬停 | `--accent-hover` |
| 发送按钮文字 | `--text-inverse` |
| 发送按钮圆角 | `radius-sm` |

---

## 4. Tailwind 配置映射

设计 Token 映射到 Tailwind `theme.extend`：

```js
// tailwind.config.js
module.exports = {
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
        'titlebar': '36px',
        'sidebar': '260px',
        'chat-header': '48px',
      },
      borderRadius: {
        'bubble': '14px',
      },
      fontSize: {
        'xs': '12px',
        'sm': '13px',
        'base': '14px',
        'md': '15px',
        'lg': '18px',
        'xl': '24px',
      },
    },
  },
};
```

## 5. 变更记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2025-07-17 | 1.0 | 初始版本，亮色主题设计 Token |
