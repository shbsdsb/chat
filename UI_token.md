# UI Token — 设计规范与组件约定

> **目的**：统一 UI 设计语言，确保新组件适配自定义 CSS 系统。
> **最后更新**：2026-07-24

---

## 一、设计 Token

### 1.1 色彩

| Token | 值 | 用途 |
|-------|-----|------|
| `color-bg-primary` | `#fff` | 主背景（main-area, bubble, drawer-body） |
| `color-bg-secondary` | `#fafafa` | 次背景（top-bar） |
| `color-bg-tertiary` | `#f5f5f5` | 三级背景（左侧会话抽屉） |
| `color-text-primary` | `#333` | 主文字 |
| `color-text-secondary` | `#555` | 次文字（按钮、标签） |
| `color-text-muted` | `#888` / `#999` | 弱化文字（占位符、辅助信息） |
| `color-border` | `#e0e0e0` | 分割线、面板边框 |
| `color-border-light` | `#d5d5d5` | 输入框/按钮边框 |
| `color-accent` | `#4a90d9` | 强调色（保存按钮、focus 边框、链接） |
| `color-danger` | `#e53935` | 危险操作（停止按钮、删除） |
| `color-bg-edit` | `#1e1e1e` | 代码编辑器背景（CSS textarea, 代码块） |
| `color-bg-edit-text` | `#d4d4d4` | 代码编辑器文字 |

### 1.2 圆角

| Token | 值 | 用途 |
|-------|-----|------|
| `radius-sm` | `6px` | 按钮、标签、小输入框 |
| `radius-md` | `8px` | 卡片、面板、会话项、预设选项 |
| `radius-lg` | `12px` | 消息气泡 |
| `radius-xl` | `24px` | 输入框 wrapper（圆形胶囊） |
| `radius-full` | `50%` | 发送按钮（圆形） |

### 1.3 间距

| Token | 值 | 用途 |
|-------|-----|------|
| `spacing-xs` | `4px` | 图标与文字间距 |
| `spacing-sm` | `8px` | 按钮组 gap、紧凑型内部间距 |
| `spacing-md` | `12px` | 列表项间距、输入栏内边距 |
| `spacing-lg` | `16px` | 抽屉标题内边距、组件间距 |
| `spacing-xl` | `24px` | 抽屉 body 内边距、页面级 padding |

### 1.4 动画

| Token | 值 | 用途 |
|-------|-----|------|
| `drawer-width-duration` | `0.2s` | 抽屉面板展开/收起 |
| `drawer-width-easing` | `ease` | 抽屉面板缓动 |
| `drawer-slide-duration` | `0.2s` | 抽屉内容页切换 |
| `drawer-slide-enter-x` | `60px` | 新内容从右侧滑入距离 |
| `drawer-slide-leave-x` | `-40px` | 旧内容向左滑出距离 |
| `title-fade-duration` | `0.15s` | 标题切换 |
| `btn-hover-duration` | `0.15s` | 按钮 hover 过渡 |
| `resizer-hover-duration` | `0.15s` | 拖拽条 hover |

### 1.5 字体

| Token | 值 | 用途 |
|-------|-----|------|
| `font-family` | `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif` | 全局 |
| `font-mono` | `"Consolas", "Monaco", "Courier New", monospace` | 代码/编辑器 |
| `font-size-xs` | `12px` | 工具栏按钮、辅助标签 |
| `font-size-sm` | `13px` | 表单文字、预设选项 |
| `font-size-md` | `14px` | 会话列表项 |
| `font-size-lg` | `15px` | 输入框、消息正文 |
| `font-size-xl` | `16px` | 抽屉标题 |

---

## 二、自定义 CSS 兼容规则

> **核心机制**：用户 CSS 通过 `_injectCss()` 注入 `<style id="custom-css">`，自动追加 `!important` 以覆盖 Vue scoped 样式。

### 2.1 新组件必须遵守

| # | 规则 | 说明 |
|---|------|------|
| 1 | **每个用户可见元素必须有稳定的 class 名** | 不能只靠 Vue scoped hash 选择器，确保用户能通过 `.your-class` 选中 |
| 2 | **class 命名遵循 BEM 风格** | 如 `conv-item`、`conv-item.active`、`btn-send`、`btn-send.is-streaming` |
| 3 | **顶级容器用组件名作 class** | 如 `.input-bar`、`.css-editor`、`.conv-item`，方便用户定位 |
| 4 | **不依赖 scoped 样式做唯一选择器** | scoped 可以保留（隔离默认样式），但 class 名必须是非嵌套的、全局可识别的 |
| 5 | **抽屉类组件必须使用 `AppDrawer` 外壳** | 不自行实现 drawer-panel/drawer-resizer/drawer-inner，统一通过父级注入 |
| 6 | **drawer.css 通过非 scoped 块导入** | `<style>@import "@/assets/drawer.css";</style>` 确保用户 CSS 可覆盖 |
| 7 | **颜色、边框等必须来自 Token** | 不硬编码颜色值，便于主题预设覆盖 |

### 2.2 组件结构模板

```vue
<template>
  <div class="my-component">
    <div class="my-component-header">
      <h3>标题</h3>
      <button class="my-component-close" @click="$emit('close')">✕</button>
    </div>
    <div class="my-component-body">
      <!-- 内容 -->
    </div>
  </div>
</template>

<script setup>
// props: visible, emit: close（如果嵌在抽屉里则由父级管理）
</script>

<style>
/* 非 scoped：引入抽屉共享样式（仅当是抽屉内容时） */
@import "@/assets/drawer.css";
</style>

<style scoped>
/* scoped：组件独有默认样式 */
.my-component { ... }
.my-component-header { ... }
</style>
```

### 2.3 不要做的事

| ❌ | 为什么 |
|----|--------|
| 只用 `<style scoped>` 而不用非 scoped 块 | 用户 CSS 即使有 `!important`，class 名也可能因 hash 变化而不稳定 |
| 把 drawer-panel 写死在组件内部 | 破坏抽屉统一架构，用户无法统一控制抽屉宽度动画 |
| 硬编码 `#fff` / `#333` 之外的独特色彩 | 应该通过 Token 变量或允许被覆盖的 class |
| 使用 `style="..."` 内联样式 | 无法被自定义 CSS 覆盖 |

---

## 三、组件库存与职责

### 3.1 外壳组件

| 组件 | 职责 | 关键 class |
|------|------|------------|
| `App.vue` | 全局布局：top-bar + app-body + 抽屉管理 | `.top-bar`, `.top-btn`, `.main-area` |
| `SettingsDrawer.vue` | 右侧可拖拽抽屉外壳（供三个设置页共用） | `.drawer-panel`, `.drawer-inner`, `.drawer-header` |
| `ConversationsDrawer.vue` | 左侧会话列表抽屉 | `.drawer-panel`（左侧）, `.conv-item`, `.btn-new-chat` |

### 3.2 内容组件

| 组件 | 所属抽屉 | 关键 class |
|------|---------|------------|
| `SettingsView.vue` | API 设置（右） | `.settings-*` |
| `ParamPresetSelector.vue` | 参数预设（右） | `.param-preset-*` |
| `CssPresetEditor.vue` | 自定义 CSS（右） | `.css-editor`, `.preset-toolbar`, `.css-textarea` |
| `CssPresetSelector.vue` | 工具栏（顶栏） | `.css-icon-btn` |

### 3.3 聊天组件

| 组件 | 职责 | 关键 class |
|------|------|------------|
| `MessageBubble.vue` | 消息气泡渲染 | `.bubble-row`, `.bubble`, `.bubble-text`, `.reasoning-block` |
| `MessageList.vue` | 消息列表容器 | `.message-list` |
| `MessageActions.vue` | 消息操作按钮 | `.message-actions` |
| `InputBar.vue` | 输入栏 | `.input-bar`, `.input-wrapper`, `.input-field`, `.btn-send` |
| `ConversationItem.vue` | 会话列表单项 | `.conv-item`, `.conv-title`, `.conv-actions` |

### 3.4 弹窗组件

| 组件 | 职责 | 关键 class |
|------|------|------------|
| `AlertDialog.vue` | 全局提示弹窗 | `.alert-dialog` |
| `BaseDialog.vue` | 通用弹窗基类 | `.base-dialog` |
| `HtmlPreview.vue` | HTML 预览 iframe | `.html-preview` |
| `ModelSelector.vue` | 模型下拉选择器 | `.model-selector` |
| `PresetSelector.vue` | API 预设列表 | `.preset-selector` |

---

## 四、主题预设

### 4.1 预设清单

| 名称 | 风格 | 核心色 |
|------|------|--------|
| 默认 | 原生样式 | — |
| 暗夜护眼 | 深色模式 | `#1a1b23` 底 / `#21222c` 面板 / `#4a6fbf` 强调 |
| 日间暖阳 | 暖色模式 | `#faf7f2` 底 / `#7a9e6b` 强调 / `#d4c9b8` 边框 |
| 小清新 | 薄荷模式 | `#f5faf7` 底 / `#7cba8a` 强调 / `#c8e0ce` 边框 |

### 4.2 预设文件

`user_data/css_presets.json`，由 `init_css_presets()` 自动创建默认预设。用户可通过 🎨 按钮进入编辑器手动创建/导入。

---

## 五、版本兼容

- 角色卡字段使用"按需识别、宽匹配"策略（详见 `Goal/product-goal.md`）
- CSS 预设 `content` 字段向后兼容：空串即无样式
- 动画 Token 变更需同步更新本文件及 `drawer.css`、`App.vue` 中的硬编码值
