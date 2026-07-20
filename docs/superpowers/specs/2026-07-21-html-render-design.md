# HTML 代码渲染 — 设计文档

> 日期：2026-07-21
> 状态：已确认

## 概述

为聊天应用添加 HTML 代码渲染能力，包含两个子功能：

1. **内联 HTML 直通** — AI 返回的 Markdown 中内嵌的安全 HTML 标签（`<div>`、`<button>`、`<table>` 等）能被浏览器直接渲染
2. **HTML 代码块预览** — ` ```html ` 代码块增加「预览」按钮，行内切换为 sandbox iframe 渲染效果（代码 ↔ 预览）

## 需求来源

用户希望在聊天界面中直接看到 AI 生成的 HTML 的可视化效果，而非只能阅读源码。

## 设计决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 方案 | B — 独立 HtmlPreview 组件 | 职责清晰、可测试、useMarkdown 改动小 |
| 安全策略 | DOMPurify 默认白名单 | 平衡功能与安全，去 script/iframe/object |
| 预览交互 | 行内切换（代码 ↔ 预览） | 不打断阅读流，比弹窗轻量 |
| 预览渲染 | sandbox iframe + srcdoc | 浏览器原生隔离，无需额外依赖 |

## 架构

### 改动文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `frontend/src/composables/useMarkdown.js` | 修改 | `html: true`；fence renderer 为 `html` 语言注入预览按钮 + `data-html-code` |
| `frontend/src/components/HtmlPreview.vue` | **新增** | 独立的 code ↔ preview 切换组件 |
| `frontend/src/components/MessageBubble.vue` | 修改 | 动态挂载 HtmlPreview；扩展事件委托 |

### 数据流

```
用户消息 → AI 返回 Markdown
                │
                ▼
     markdown-it (html: true)   ← 内联 HTML 标签现在会通过
                │
                ▼
          DOMPurify 清洗        ← 默认白名单
                │
                ▼
         v-html 渲染到气泡      ← 安全的内联 HTML 可见

━━━━━━ HTML 代码块分支 ━━━━━

  fence renderer 检测 lang 以 "html" 开头
         │
         ▼
  输出带 data-html-code 的标记
  + 预览切换按钮
         │
         ▼
  MessageBubble onMounted/watch 后
  查找占位标记，动态挂载 HtmlPreview
         │
         ▼
  HtmlPreview 组件
  ├─ code 模式：<pre><code>（hljs 高亮）
  └─ preview 模式：<iframe sandbox="allow-scripts" srcdoc="...">
```

## 组件设计

### useMarkdown.js 改动

```diff
- html: false,
+ html: true,     // 允许内联 HTML 标签通过 markdown-it
```

fence renderer 中，当 `lang` 以 `html` 开头时，在 wrapper 上添加 `data-html-code` 属性（存储 Base64 编码后的原始 HTML，避免引号/换行等特殊字符破坏 HTML 属性）和预览切换按钮。

### HtmlPreview.vue（新增）

```
Props:
  code: string    — 原始 HTML 代码字符串

内部状态:
  mode: 'code' | 'preview'   — 默认 'code'

Template:
  .html-preview-block
    .preview-toolbar
      button[预览]  — 切换到 preview
      button[代码]  — 切换回 code
      button[复制]  — 保留复制功能
    pre > code       — v-show="mode === 'code'"
    iframe           — v-show="mode === 'preview'"
      sandbox="allow-scripts"
      :srcdoc="code"
      @load="autoResize"
```

- iframe 不设置 `allow-same-origin`，确保沙箱隔离
- `autoResize`：通过 `iframe.contentDocument.body.scrollHeight` 自适应高度

### MessageBubble.vue 改动

1. **动态挂载**：在 `onMounted` 和 `watch(frozenHtmls)` 中，查找 `.code-block-wrapper[data-html-code]`，用 `createApp(HtmlPreview, { code })` 挂载到每个节点
2. **清理**：`onBeforeUnmount` / watch 前先 `app.unmount()` 旧实例
3. **事件委托**：保留现有 `onBubbleClick` 复制逻辑，无需额外处理预览（HtmlPreview 自管理）

## 安全模型

### 内联 HTML

```
markdown-it 输出 → DOMPurify.sanitize() → v-html
```

DOMPurify 默认白名单自动去除：
- `<script>`、`<iframe>`、`<object>`、`<embed>`
- `onerror`、`onload` 等事件属性
- `javascript:` 协议

### 代码块预览

```
原始 HTML → iframe sandbox="allow-scripts" srcdoc
```

- 不设 `allow-same-origin`：无法访问主页面 Cookie/localStorage
- 不设 `allow-top-navigation`：无法跳转顶层页面
- 仅 `allow-scripts`：允许 HTML 中的 JS 在沙箱内执行

## 边界情况

| 场景 | 处理 |
|------|------|
| HTML 代码为空 | 预览显示空白页 |
| 超长 HTML（>100KB） | 使用 `blob:` URL 替代直接 srcdoc（避免 URL 长度限制） |
| 流式输出中代码块未闭合 | fence renderer 只在完整 fence 时触发，未闭合不显示 |
| 非 HTML 代码块 | 不受影响，保持现有 code-block-wrapper 行为 |
| 多个 HTML 代码块 | 各自独立的 HtmlPreview 实例，互不干扰 |
| 消息更新/重新生成 | watch 中先 unmount 旧实例，再挂载新实例 |

## 测试要点

1. 内联 HTML：MD 中包含 `<div style="color:red">` 应渲染为红色文字
2. 内联 HTML 安全：`<script>alert(1)</script>` 应被 DOMPurify 去除
3. HTML 代码块预览：` ```html ` 块旁出现预览按钮，点击切换为渲染视图
4. 非 HTML 代码块无预览按钮
5. 多个 HTML 代码块独立切换
6. 流式输出时 HTML 块闭合后才显示预览按钮
7. 复制按钮在预览模式下仍可用
