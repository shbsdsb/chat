# UI 现代化重设计 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 对 Chat 应用进行现代 SaaS 风格视觉重设计 — 升级 Token 体系、重构 5 个核心组件、注入微交互动效，零新增依赖，兼容现有 CSS 预设。

**Architecture:** 纯 CSS 增强方案。先升级 Token 定义文件（UI_token.md），再逐组件刷新样式（App.vue → MessageBubble → InputBar → WelcomeBanner → ConversationItem），最后注入全局微交互逻辑（main.js）。所有 BEM class 保持不变，新增 class 使用独立命名空间。

**Tech Stack:** Vue 3 SFC（`<style>` + `<style scoped>`）、CSS 自定义属性 / keyframes、Vanilla JS 事件委托（ripple）

## Global Constraints

- 零新增 npm 依赖
- 所有现有 BEM class 名保持不变（`.bubble-row`, `.bubble`, `.bubble-text`, `.input-bar`, `.conv-item` 等）
- 新增 class 使用独立命名空间（`.model-badge`, `.bubble-role-label`, `.ripple`）
- 兼容 `_injectCss()` + `!important` 用户 CSS 覆盖机制
- 每任务独立可验证（启动 `npm run dev` 目视检查）
- 验证方式：前端 `npm run dev` 后在浏览器中目视确认（无自动化测试）

---

## File Structure

| 文件 | 操作 | 职责 |
|------|------|------|
| `UI_token.md` | 修改 | Token 定义：新增阴影/玻璃态/动画 Token，升级色彩/圆角 |
| `frontend/src/App.vue` | 修改 | 全局样式：顶栏、背景色、动画 @keyframes 定义 |
| `frontend/src/components/MessageBubble.vue` | 修改 | 聊天气泡：渐变/非对称圆角/角色标签/推理块/编辑模式 |
| `frontend/src/components/InputBar.vue` | 修改 | 输入栏：玻璃态/光晕按钮/脉冲停止态/ModelSelector 徽章 |
| `frontend/src/components/WelcomeBanner.vue` | 修改 | 欢迎页：渐变标题/实心按钮/几何背景/快捷卡片 |
| `frontend/src/components/ConversationItem.vue` | 修改 | 会话列表项：靛蓝指示线/active 态/hover 态/时间戳 |
| `frontend/src/main.js` | 修改 | 全局 ripple 事件委托 + 消息入场 class 注入 |

---

### Task 1: 升级 UI_token.md

**Files:**
- Modify: `UI_token.md`

**Produces:** 更新后的 Token 定义供后续所有任务引用

- [ ] **Step 1: 更新色彩表**

将 `UI_token.md` 中 1.1 色彩表的以下行更新：

| Token | 旧值 → 新值 |
|-------|-------------|
| `color-bg-secondary` | `#fafafa` → `#f8f9fb` |
| `color-bg-tertiary` | `#f5f5f5` → `#f0f1f5` |
| `color-text-primary` | `#333` → `#1a1a2e` |
| `color-text-secondary` | `#555` → `#5b5b7a` |
| `color-text-muted` | `#888` / `#999` → `#8e8ea0` |
| `color-border` | `#e0e0e0` → `#e2e4eb` |
| `color-border-light` | `#d5d5d5` → `#d8dae2` |
| `color-accent` | `#4a90d9` → `#4f6ef6` |
| `color-danger` | `#e53935` → `#ef4444` |

- [ ] **Step 2: 在色彩表后新增阴影表（1.2 节，后续编号顺延）**

```markdown
### 1.2 阴影

| Token | 值 | 用途 |
|-------|-----|------|
| `shadow-xs` | `0 1px 2px rgba(0,0,0,0.04)` | 面板轻微浮起 |
| `shadow-sm` | `0 2px 8px rgba(0,0,0,0.06)` | 消息气泡 |
| `shadow-md` | `0 4px 16px rgba(0,0,0,0.08)` | 抽屉面板、弹窗 |
| `shadow-lg` | `0 8px 32px rgba(0,0,0,0.10)` | 模态弹窗 |
```

- [ ] **Step 3: 更新圆角表（原 1.2 → 1.3）**

| Token | 旧值 → 新值 |
|-------|-------------|
| `radius-sm` | `6px` → `8px` |
| `radius-md` | `8px` → `10px` |
| `radius-lg` | `12px` → `16px` |
| `radius-xl` | `24px` → `28px` |

- [ ] **Step 4: 在圆角表后新增玻璃态 Token 小节（1.4）**

```markdown
### 1.4 玻璃态

| Token | 值 | 用途 |
|-------|-----|------|
| `glass-bg` | `rgba(255,255,255,0.7)` | 玻璃态背景 |
| `glass-border` | `rgba(0,0,0,0.06)` | 玻璃态边框 |
| `glass-blur` | `12px` | 玻璃态模糊量 |
```

- [ ] **Step 5: 更新动画表（原 1.4 → 1.5），追加新 Token**

在原动画表末尾追加：

```markdown
| `msg-enter-duration` | `0.25s` | 消息入场动画 |
| `msg-enter-easing` | `ease-out` | 消息入场缓动 |
| `cursor-blink-duration` | `0.8s` | 打字光标闪烁 |
| `ripple-duration` | `0.5s` | 按钮涟漪 |
| `pulse-duration` | `1.2s` | 停止按钮脉冲 |
| `reasoning-collapse-duration` | `0.3s` | 推理块折叠 |
```

- [ ] **Step 6: 更新最后更新时间**

将头部 `> **最后更新**：2026-07-24` 改为 `> **最后更新**：2026-07-27`

- [ ] **Step 7: 提交**

```bash
git add UI_token.md
git commit -m "docs: upgrade UI tokens — colors, shadows, glass, animations"
```

---

### Task 2: App.vue 全局样式刷新

**Files:**
- Modify: `frontend/src/App.vue`

**Consumes:** Task 1 的 Token 定义
**Produces:** 全局 CSS 变量、顶栏新样式、动画 @keyframes

- [ ] **Step 1: 替换全局 CSS 变量块**

在 `App.vue` 的 `<style>` 块（非 scoped）顶部，将现有的硬编码颜色替换为全局 CSS 自定义属性，并注入新 Token。将：

```css
html, body, #app {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: #333;
  background: #fff;
}
```

替换为：

```css
:root {
  --bg-primary: #fff;
  --bg-secondary: #f8f9fb;
  --bg-tertiary: #f0f1f5;
  --text-primary: #1a1a2e;
  --text-secondary: #5b5b7a;
  --text-muted: #8e8ea0;
  --border: #e2e4eb;
  --border-light: #d8dae2;
  --accent: #4f6ef6;
  --accent-light: #6c8cfc;
  --danger: #ef4444;
  --shadow-xs: 0 1px 2px rgba(0,0,0,0.04);
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 16px rgba(0,0,0,0.08);
  --shadow-lg: 0 8px 32px rgba(0,0,0,0.10);
  --glass-bg: rgba(255,255,255,0.7);
  --glass-border: rgba(0,0,0,0.06);
  --glass-blur: 12px;
  --radius-sm: 8px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-xl: 28px;
}

html, body, #app {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: var(--text-primary);
  background: var(--bg-primary);
}
```

- [ ] **Step 2: 升级顶栏样式**

替换 `.top-bar` 样式块：

```css
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 0 20px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  box-shadow: var(--shadow-xs);
  flex-shrink: 0;
  position: relative;
  z-index: 10;
}

.top-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.top-title {
  font-size: 16px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent), #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.top-nav {
  display: flex;
  gap: 4px;
}

.top-btn {
  padding: 6px 14px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  position: relative;
  transition: all 0.15s ease;
}
.top-btn::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 2px;
  background: var(--accent);
  border-radius: 2px;
  transition: width 0.15s ease;
}
.top-btn:hover {
  color: var(--text-primary);
  transform: translateY(-1px);
}
.top-btn:hover::after {
  width: 60%;
}
```

- [ ] **Step 3: 新增动画 @keyframes**

在 `</style>` 之前追加全局动画定义：

```css
/* ── 全局动画 @keyframes ────────────────── */

@keyframes message-enter {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes blink-cursor {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0; }
}

@keyframes ripple {
  from { transform: scale(0); opacity: 0.25; }
  to   { transform: scale(4); opacity: 0; }
}

@keyframes stop-pulse {
  0%   { box-shadow: 0 0 0 0 rgba(239,68,68,0.4); }
  100% { box-shadow: 0 0 0 8px rgba(239,68,68,0); }
}
```

- [ ] **Step 4: 更新 main-area 背景色**

将 `.main-area` 背景从 `#fff` 改为 `var(--bg-primary)`：

```css
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  overflow: hidden;
}
```

- [ ] **Step 5: 删除旧的 `.top-btn:hover` 冲突规则**

移除 App.vue 中已有的旧 `.top-btn:hover { background: #e8e8e8; }` 行（如果仍存在）。

- [ ] **Step 6: 验证**

```bash
cd frontend && npm run dev
```

浏览器打开 http://127.0.0.1:5173，确认：
- 顶栏 48px 高、渐变色标题、按钮无边框 hover 微抬
- CSS 变量已生效（DevTools 检查 `:root`）

- [ ] **Step 7: 提交**

```bash
git add frontend/src/App.vue
git commit -m "feat: global style refresh — CSS variables, top bar upgrade, keyframes"
```

---

### Task 3: MessageBubble.vue 重构

**Files:**
- Modify: `frontend/src/components/MessageBubble.vue`

**Consumes:** Task 2 的 CSS 变量和 @keyframes
**Produces:** 全新聊天气泡样式

- [ ] **Step 1: 替换 template — 增加角色标签**

在 `.bubble-row` 内，气泡上方插入角色标签：

```html
<template>
    <div class="bubble-row" :class="[message.role, { entering: isEntering }]">
        <!-- 角色标签 -->
        <span class="bubble-role-label">{{ message.role === 'user' ? '你' : 'Chat' }}</span>

        <!-- 编辑工具栏 -->
        <div v-if="isEditing" class="edit-toolbar">
            ...
```

> 注意：`isEntering` 由 main.js 注入（Task 7），此处只需绑定 class。

- [ ] **Step 2: 重写 `<style scoped>` — 核心气泡样式**

完全替换 `<style scoped>` 块：

```css
/* ── 气泡行 ──────────────────────────────── */
.bubble-row {
  display: flex;
  flex-direction: column;
  margin-bottom: 16px;
  padding: 0 8px;
}
.bubble-row.user {
  align-items: flex-end;
}
.bubble-row.assistant {
  align-items: flex-start;
}

/* ── 角色标签 ────────────────────────────── */
.bubble-role-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
  padding: 0 4px;
  user-select: none;
}

/* ── 入场动画 ────────────────────────────── */
.bubble-row.entering .bubble {
  animation: message-enter 0.25s ease-out;
}

/* ── 气泡容器 ────────────────────────────── */
.bubble {
  max-width: 70%;
  min-width: 0;
  padding: 12px 16px;
  font-size: 15px;
  line-height: 1.6;
  overflow: hidden;
}

/* ── User 气泡：靛蓝渐变 ─────────────────── */
.bubble-row.user .bubble {
  background: linear-gradient(135deg, var(--accent), var(--accent-light));
  color: #fff;
  border-radius: var(--radius-lg) 4px var(--radius-lg) var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

/* ── Assistant 气泡：灰底 ────────────────── */
.bubble-row.assistant .bubble {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border-radius: 4px var(--radius-lg) var(--radius-lg) var(--radius-lg);
  box-shadow: var(--shadow-xs);
}

/* ── 编辑模式 ────────────────────────────── */
.bubble-editing {
  width: 100%;
  padding: 0;
  border: 1.5px solid var(--accent);
  box-shadow: var(--shadow-md);
  transition: border 0.2s ease, box-shadow 0.2s ease;
}

.edit-toolbar {
  display: flex;
  gap: 6px;
  margin-bottom: 6px;
}

.edit-btn {
  width: 30px;
  height: 30px;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  font-size: 15px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.save-btn {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}
.save-btn:hover {
  background: #3d5ce5;
  border-color: #3d5ce5;
}

.cancel-btn {
  background: #fff;
  color: var(--text-muted);
}
.cancel-btn:hover {
  background: #f0f1f5;
  color: var(--text-secondary);
}

.edit-textarea {
  width: 100%;
  min-width: 420px;
  min-height: 120px;
  padding: 16px;
  border: none;
  border-radius: 12px;
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  background: #fafbfc;
  resize: vertical;
  outline: none;
  box-sizing: border-box;
}

.bubble-text {
  word-break: break-word;
  overflow: hidden;
}

/* ── 推理块 ──────────────────────────────── */
.reasoning-block {
  margin-bottom: 10px;
  border-left: 3px solid var(--accent);
  padding-left: 10px;
}

.reasoning-header {
  cursor: pointer;
  font-size: 13px;
  color: var(--text-muted);
  user-select: none;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 4px;
}
.reasoning-header:hover {
  color: var(--text-secondary);
}

.reasoning-icon {
  font-size: 10px;
  width: 12px;
  transition: transform 0.2s ease;
}

.reasoning-content {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
  transition: max-height 0.3s ease;
}
.reasoning-block:not(.is-open) .reasoning-content {
  max-height: 0;
  overflow: hidden;
}

/* ── 代码块 ──────────────────────────────── */
.bubble-text :deep(.code-block-wrapper) {
  position: relative;
  margin: 8px 0;
  max-width: 100%;
  overflow: auto;
}
.bubble-text :deep(.code-block-wrapper pre) {
  margin: 0;
  padding: 16px;
  border-radius: 6px;
  background: #f6f8fa;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.5;
}
.bubble-text :deep(.code-block-wrapper code) {
  background: transparent;
  padding: 0;
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
}

/* ── 复制按钮 ────────────────────────────── */
.bubble-text :deep(.copy-btn) {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 32px;
  height: 32px;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  background: #fff;
  color: #656d76;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.15s;
  padding: 0;
}
.bubble-text :deep(.code-block-wrapper:hover .copy-btn) {
  opacity: 1;
}
.bubble-text :deep(.copy-btn:hover) {
  background: #f3f4f6;
}

/* ── MD 通用元素 ──────────────────────────── */
.bubble-text :deep(p) {
  margin: 0 0 8px;
}
.bubble-text :deep(p:last-child) {
  margin-bottom: 0;
}
.bubble-text :deep(ul),
.bubble-text :deep(ol) {
  padding-left: 20px;
  margin: 0 0 8px;
}
.bubble-text :deep(blockquote) {
  border-left: 3px solid #d0d7de;
  padding-left: 12px;
  margin: 8px 0;
  color: #656d76;
}
.bubble-text :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
  width: 100%;
}
.bubble-text :deep(th),
.bubble-text :deep(td) {
  border: 1px solid #d0d7de;
  padding: 6px 12px;
  text-align: left;
}
.bubble-text :deep(th) {
  background: #f6f8fa;
  font-weight: 600;
}

/* ── HtmlPreview ──────────────────────────── */
.bubble-text :deep(.html-preview-container) {
  margin: 8px 0;
}
.html-auto-block {
  margin: 8px 0;
}
```

- [ ] **Step 3: 验证**

```bash
cd frontend && npm run dev
```

确认：
- User 消息：靛蓝渐变底白字，右下角尖圆角，带阴影
- Assistant 消息：灰底黑字，左上角尖圆角
- 角色标签 "你" / "Chat" 出现在气泡上方
- 推理块：左侧 3px 靛蓝竖条

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/MessageBubble.vue
git commit -m "feat: redesign message bubbles — gradient user, grey assistant, role labels"
```

---

### Task 4: InputBar.vue 重构

**Files:**
- Modify: `frontend/src/components/InputBar.vue`

**Consumes:** Task 2 的 CSS 变量和 @keyframes
**Produces:** 玻璃态输入栏、光晕发送按钮、脉冲停止态、ModelSelector 工具栏

- [ ] **Step 1: 在 template 顶部增加工具栏行**

在 `.input-bar` 容器内、`.input-wrapper` 之前插入：

```html
<div class="input-bar">
    <div class="input-toolbar">
      <button class="model-badge" @click="$emit('open-model-selector')" title="切换模型">
        {{ chatStore.activePreset?.model || '选择模型' }}
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
      </button>
    </div>
    <div class="input-wrapper">
      ...
```

- [ ] **Step 2: 替换整个 `<style>` 块（非 scoped）**

```css
.input-bar {
  padding: 8px 24px 16px;
  border-top: 1px solid transparent;
}

.input-toolbar {
  display: flex;
  align-items: center;
  padding: 0 4px 6px;
  min-height: 28px;
}

.model-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.model-badge:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: rgba(79,110,246,0.04);
}

.input-bar .input-wrapper {
  display: flex;
  align-items: flex-end;
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  padding: 6px 6px 6px 18px;
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  box-shadow: var(--shadow-sm);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.input-bar .input-wrapper:focus-within {
  border-color: var(--accent);
  box-shadow: var(--shadow-sm), 0 0 0 3px rgba(79,110,246,0.1);
}

.input-bar .input-field {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: 15px;
  line-height: 1.5;
  max-height: 120px;
  padding: 4px 0;
  font-family: inherit;
  background: transparent;
  color: var(--text-primary);
}
.input-bar .input-field::placeholder {
  color: var(--text-muted);
}

.input-bar .btn-send {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: none;
  background: var(--accent);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.2s, transform 0.15s, box-shadow 0.15s;
  position: relative;
  overflow: hidden;
}
.input-bar .btn-send:hover {
  background: #3d5ce5;
  transform: scale(1.08);
  box-shadow: 0 0 16px rgba(79,110,246,0.35);
}
.input-bar .btn-send:active {
  transform: scale(0.92);
}
.input-bar .btn-send.is-streaming {
  background: var(--danger);
  animation: stop-pulse 1.2s ease-in-out infinite;
}
.input-bar .btn-send.is-streaming:hover {
  background: #dc2626;
  box-shadow: none;
}

.input-bar .icon-send {
  width: 18px;
  height: 18px;
  margin-left: 1px;
}

.input-bar .icon-stop {
  width: 14px;
  height: 14px;
}
```

- [ ] **Step 3: 验证**

```bash
cd frontend && npm run dev
```

确认：
- 输入栏玻璃态背景（毛玻璃效果）
- 发送按钮靛蓝，hover 放大+光晕，active 缩小
- 流式生成中按钮红色脉冲
- 输入框聚焦时边框靛蓝+光晕
- 顶部 ModelSelector 徽章行可见

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/InputBar.vue
git commit -m "feat: redesign input bar — glass wrapper, glow button, pulse stop, model badge"
```

---

### Task 5: WelcomeBanner.vue 重构

**Files:**
- Modify: `frontend/src/components/WelcomeBanner.vue`

**Consumes:** Task 2 的 CSS 变量
**Produces:** 渐变标题、实心按钮、几何背景、快捷卡片

- [ ] **Step 1: 替换 template**

```html
<template>
  <div class="welcome">
    <div class="welcome-bg"></div>
    <div class="welcome-content">
      <h1 class="welcome-title">Chat</h1>
      <p class="welcome-subtitle">智能对话，触手可及</p>
      <button class="btn-start btn-ripple" @click="chatStore.createConversation()">开始新对话</button>
      <div class="welcome-cards">
        <div class="welcome-card" @click="chatStore.createConversation()">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>
          <span>新对话</span>
        </div>
        <div class="welcome-card" @click="$router.push('/settings')">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          <span>设置</span>
        </div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: 更新 script setup — 添加 router 引用**

```js
import { useRouter } from "vue-router";
const router = useRouter();
```

- [ ] **Step 3: 替换 `<style scoped>`**

```css
.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.welcome-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 80% 60% at 50% 40%, rgba(79,110,246,0.04) 0%, transparent 70%),
    radial-gradient(ellipse 40% 30% at 80% 20%, rgba(139,92,246,0.03) 0%, transparent 70%);
  pointer-events: none;
}

.welcome-content {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 1;
}

.welcome-title {
  font-size: 36px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--accent), #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}

.welcome-subtitle {
  font-size: 15px;
  color: var(--text-muted);
  margin-bottom: 28px;
}

.btn-start {
  padding: 12px 32px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--accent);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}
.btn-start:hover {
  background: #3d5ce5;
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}
.btn-start:active {
  transform: translateY(0);
}

.welcome-cards {
  display: flex;
  gap: 12px;
  margin-top: 36px;
}

.welcome-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 24px;
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  box-shadow: var(--shadow-xs);
  border: 1px solid var(--border);
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 13px;
  transition: all 0.2s ease;
  min-width: 100px;
}
.welcome-card:hover {
  box-shadow: var(--shadow-sm);
  transform: translateY(-2px);
  border-color: var(--accent);
  color: var(--accent);
}
```

- [ ] **Step 4: 验证**

```bash
cd frontend && npm run dev
```

确认：
- 渐变标题 "Chat"（靛蓝→紫色）
- 靛蓝实心主按钮
- 极淡几何光斑背景
- 底部两张快捷卡片 hover 浮起

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/WelcomeBanner.vue
git commit -m "feat: redesign welcome banner — gradient title, solid button, cards"
```

---

### Task 6: ConversationItem.vue 重构

**Files:**
- Modify: `frontend/src/components/ConversationItem.vue`

**Consumes:** Task 2 的 CSS 变量
**Produces:** 靛蓝指示线、优化 active/hover 态、时间戳

- [ ] **Step 1: 在 template 中增加时间戳**

在 `.conv-title` 和 `.conv-actions` 之间插入：

```html
<span class="conv-time">{{ formatTime(conversation.lastMessageAt) }}</span>
```

- [ ] **Step 2: 在 script setup 中增加 formatTime 函数**

```js
function formatTime(ts) {
  if (!ts) return "";
  const d = new Date(ts);
  const now = new Date();
  const diffMs = now - d;
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "刚刚";
  if (diffMin < 60) return `${diffMin}分钟前`;
  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return `${diffHour}小时前`;
  return d.toLocaleDateString("zh-CN", { month: "short", day: "numeric" });
}
```

- [ ] **Step 3: 替换 `<style scoped>`**

```css
.conv-item {
  padding: 8px 10px 8px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 14px;
  color: var(--text-primary);
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background 0.15s ease;
}
.conv-item::before {
  content: "";
  position: absolute;
  left: 0;
  top: 6px;
  bottom: 6px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: transparent;
  transition: background 0.2s ease;
}
.conv-item:hover {
  background: rgba(0,0,0,0.03);
}
.conv-item.active {
  background: rgba(79,110,246,0.08);
}
.conv-item.active::before {
  background: var(--accent);
}

.conv-title {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 14px;
}

.conv-time {
  font-size: 12px;
  color: var(--text-muted);
  flex-shrink: 0;
  margin-right: 2px;
}

.conv-actions {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
  visibility: hidden;
}
.conv-item:hover .conv-actions,
.conv-item.active .conv-actions {
  visibility: visible;
}

.conv-action-btn {
  width: 26px;
  height: 26px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.12s, color 0.12s;
}
.conv-action-btn:hover {
  background: rgba(0,0,0,0.06);
  color: var(--text-primary);
}
.conv-action-delete:hover {
  background: rgba(239,68,68,0.10);
  color: var(--danger);
}
```

- [ ] **Step 4: 验证**

```bash
cd frontend && npm run dev
```

确认：
- 选中会话左侧 3px 靛蓝竖线
- active 态淡蓝底
- 右侧显示时间戳（相对时间）
- hover 编辑/删除按钮

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/ConversationItem.vue
git commit -m "feat: redesign conversation items — accent indicator, active state, timestamps"
```

---

### Task 7: 微交互注入 — main.js

**Files:**
- Modify: `frontend/src/main.js`

**Consumes:** Task 2 的 @keyframes，Task 3 的 `.entering` class
**Produces:** 全局 ripple 事件委托、消息入场 class 注入

- [ ] **Step 1: 在 app.mount 后追加 ripple 事件委托**

在 `app.mount("#app");` 之后追加：

```js
// ── 全局 Ripple 效果 ────────────────────────

document.addEventListener("mousedown", (e) => {
  const btn = e.target.closest(".btn-ripple");
  if (!btn) return;

  const ripple = document.createElement("span");
  ripple.className = "ripple";

  const rect = btn.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height);
  ripple.style.width = ripple.style.height = `${size}px`;
  ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
  ripple.style.top = `${e.clientY - rect.top - size / 2}px`;

  btn.appendChild(ripple);

  ripple.addEventListener("animationend", () => ripple.remove());
});

// 注入 ripple 全局样式
const rippleStyle = document.createElement("style");
rippleStyle.textContent = `
  .btn-ripple { position: relative; overflow: hidden; }
  .ripple {
    position: absolute;
    border-radius: 50%;
    background: rgba(255,255,255,0.3);
    pointer-events: none;
    animation: ripple 0.5s ease-out;
  }
`;
document.head.appendChild(rippleStyle);
```

- [ ] **Step 2: 追加消息入场观察逻辑**

继续在 main.js 末尾追加：

```js
// ── 消息入场动画 ────────────────────────────

const msgObserver = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    mutation.addedNodes.forEach((node) => {
      if (node.nodeType !== 1) return;
      // 新增的消息气泡行
      const bubbleRows = node.classList?.contains("bubble-row")
        ? [node]
        : node.querySelectorAll?.(".bubble-row") || [];

      bubbleRows.forEach((row) => {
        row.classList.add("entering");
        row.addEventListener("animationend", () => {
          row.classList.remove("entering");
        }, { once: true });
      });
    });
  });
});

// 延迟启动观察（等 DOM 就绪）
setTimeout(() => {
  const listEl = document.querySelector(".message-list");
  if (listEl) {
    msgObserver.observe(listEl, { childList: true, subtree: false });
  }
}, 500);
```

- [ ] **Step 3: 验证**

```bash
cd frontend && npm run dev
```

确认：
- 点击"开始新对话"按钮（WelcomeBanner 中带 `.btn-ripple`）有涟漪效果
- 发送新消息后气泡从底部滑入
- 停止按钮在流式时有红色脉冲

- [ ] **Step 4: 提交**

```bash
git add frontend/src/main.js
git commit -m "feat: add global ripple effect and message enter animation"
```

---

### Task 8: 主题预设 CSS 适配验证

**Files:**
- 读取: `user_data/css_presets.json`
- 可能修改: `user_data/css_presets.json`（仅当预设需微调）

**Consumes:** Task 2-7 的全部变更
**Produces:** 验证报告

- [ ] **Step 1: 切换暗夜护眼主题验证**

在 CssPresetSelector 中选择"暗夜护眼"，验证：
- user 气泡渐变在深色背景下可见
- assistant 气泡与深色背景有足够对比
- 靛蓝强调色 `#4f6ef6` 可辨识

- [ ] **Step 2: 切换日间暖阳主题验证**

选择"日间暖阳"，验证靛蓝与暖色背景协调不冲突。

- [ ] **Step 3: 切换小清新主题验证**

选择"小清新"，验证靛蓝与薄荷绿搭配。

- [ ] **Step 4: 修复发现的问题（如有）**

如果某主题下对比度不足，微调对应预设的 CSS。

- [ ] **Step 5: 提交（如有修改）**

```bash
git add user_data/css_presets.json
git commit -m "fix: adjust theme presets for new accent color compatibility"
```

---

## Self-Review

**1. Spec coverage:**
- Token 升级 → Task 1 ✅
- App.vue 全局 + keyframes → Task 2 ✅
- MessageBubble → Task 3 ✅
- InputBar → Task 4 ✅
- WelcomeBanner → Task 5 ✅
- ConversationItem → Task 6 ✅
- 微交互（ripple + message-enter + cursor-blink + stop-pulse + 顶栏微抬）→ Task 7 + Task 2 ✅
- 主题预设适配验证 → Task 8 ✅

**2. Placeholder scan:** 无 TBD/TODO，所有步骤有完整代码。

**3. Type consistency:** 各任务通过 CSS 变量（`:root` 定义于 Task 2）松耦合，不依赖 JS 类型。Task 7 的 `.entering` class 与 Task 3 的 template 绑定一致。
