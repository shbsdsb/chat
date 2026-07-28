# CSS预设 / 对话栏 / 主对话页 — 设计规格

> **日期**：2026-07-27 · **状态**：已确认 · **预览**：`temp_mainui/index.html`

## 1. 目标

将 CssPresetEditor、ConversationsDrawer/ConversationItem、Home/MessageBubble/InputBar 改为 CSS 变量驱动，统一 border-radius、focus 环、disabled opacity，与已改造页面视觉一致。

## 2. CSS 预设页面 (CssPresetEditor)

### 改动
- 整体包装为 `.card`（与 API 设置一致），header 用 palette 图标 + "CSS 主题" label
- 工具栏：预设下拉 → `input-field` 样式 + focus-ring；新建 → accent `btn-sm primary`；重命名/删除 → `icon-btn`
- CSS textarea：保持深色编辑器（`bg: #1e1e1e`, `color: #d4d4d4`），`border-radius: var(--radius-sm)`，focus 蓝光环
- 底部按钮：重置 → `btn-sm outline`；保存 → `btn-sm primary`
- 所有硬编码颜色 → CSS 变量

## 3. 会话栏 (ConversationsDrawer + ConversationItem)

### ConversationsDrawer
- `background: #f5f5f5` → `var(--bg-tertiary)`
- `border-right: #e0e0e0` → `var(--border)`
- `color: #333` → `var(--text-primary)`
- `btn-new-chat`: `bg: var(--bg-primary)`, `border: var(--border-light)`, `border-radius: var(--radius-sm)`, hover `bg: var(--bg-input-hover)`

### ConversationItem
- action-btn `border-radius: 6px` → `var(--radius-sm)`
- action-btn hover `background: rgba(0,0,0,0.06)` → `var(--bg-input-hover)`
- delete hover `background: rgba(239,68,68,0.10)` → `var(--danger-bg)`
- 其余已用 CSS 变量，无需改动

## 4. 主对话页 (MessageBubble + InputBar)

### MessageBubble
- 编辑按钮 save/cancel → CSS 变量（`var(--accent)`, `var(--bg-primary)`, `var(--border-light)`）
- 编辑 textarea `min-width: 420px` → `min-height: 100px`（弹性宽度）
- 代码块 `:deep()` → `background: var(--code-bg)`, `color: var(--code-text)`
- 复制按钮 → `border: 1px solid var(--border)`, `border-radius: var(--radius-sm)`
- blockquote `border-left-color` → `var(--border-light)`, `color` → `var(--text-secondary)`
- table `th` `background` → `var(--bg-secondary)`, `border-color` → `var(--border-light)`

### InputBar
- `align-items: flex-end` → `center`（修复文字偏下问题）
- send button hover `background: #3d5ce5` → `var(--accent-light)`
- is-streaming hover `background: #dc2626` → CSS 变量

## 5. 实施范围

| 文件 | 改动 |
|------|------|
| `CssPresetEditor.vue` | 卡片包装 + 全变量化 |
| `ConversationsDrawer.vue` | 颜色变量化 |
| `ConversationItem.vue` | action-btn border-radius + hover 变量化 |
| `InputBar.vue` | align-items center + hover 颜色变量化 |
| `MessageBubble.vue` | 编辑/代码块/blockquote 变量化, min-width 修复 |
| `Home.vue` | 无需改动 |

**全部使用 scoped 样式 + CSS 变量，零硬编码。**

## 6. 审查

| 日期 | 审查者 | 结果 |
|------|--------|------|
| 2026-07-27 | 用户（可视化预览） | ✅ 输入框居中修复后确认 |
