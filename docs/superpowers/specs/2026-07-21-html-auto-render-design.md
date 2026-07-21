# 自动 HTML 渲染支持 — 设计规格

**日期**: 2026-07-21  
**状态**: 设计完成，待实现  
**标签**: 1.1.3

---

## 1. 目标

AI 回复中输出的 HTML 内容（完整文档或片段）自动渲染为可视化效果，无需用户手动切换到预览模式。现有 ````html` 代码块机制保持不变。

### 1.1 场景

| 场景 | AI 输出示例 | 期望行为 |
|------|------------|---------|
| 完整 HTML 文档 | `<!DOCTYPE html><html>...` | 整条消息用 iframe 直接渲染 |
| HTML 片段嵌在文本中 | 一段文字 + `<div class="card">...</div>` + 一段文字 | 文本部分 markdown 渲染，HTML 部分 iframe 渲染，上下排列 |
| 纯 Markdown | 无 HTML | 现有流程，完全不变 |
| ````html` 代码块 | ````html\n...\n``` | 现有流程（代码/预览切换），完全不变 |

---

## 2. 架构

```
AI 原始回复
    │
    ▼
useMarkdown.js ─── detectHtmlType(content)
    │
    ├── "full"  → blocks = [{type:"html", code:content}]
    ├── "mixed" → blocks = [{type:"text", html:...}, {type:"html", code:...}, ...]
    └── "none"  → 现有流程（frozenHtmls + liveHtml）
    │
    ▼
MessageBubble.vue
    ├── text block → <div v-html="block.html" />
    └── html block → <HtmlPreview :code="block.code" :showToggle="false" />
```

**改动文件（3 个）：**

| 文件 | 改动 |
|------|------|
| `frontend/src/composables/useMarkdown.js` | 新增 `detectHtmlType()`、`splitMixed()`；导出 `blocks` + `isCompleteHtml` |
| `frontend/src/components/MessageBubble.vue` | 按 block 类型条件渲染 |
| `frontend/src/components/HtmlPreview.vue` | 新增 prop `showToggle`（默认 true），false 时隐藏切换栏 |

**不改动：** 后端、chat store、router、其他组件。

---

## 3. HTML 检测规则

### 3.1 detectHtmlType(content)

```
detectHtmlType(content)
    │
    ├── "full"   trim 后以 <!DOCTYPE html> 或 <html 开头（忽略大小写）
    │
    ├── "mixed"  非完整文档，但存在 ≥1 个可提取的块级 HTML 容器
    │
    └── "none"   其他情况，走现有流程
```

### 3.2 触发提取的标签（白名单）

```
div, section, article, header, footer, nav, main, aside,
table, form, fieldset, details, figure, ul, ol, dl
```

不触发提取的行内/小标签：`span, a, p, h1-h6, img, button, input, select, textarea, label, strong, em, code, pre, br, hr, li, td, th, tr` 等。

### 3.3 片段质量门槛

HTML 片段必须满足：≥ 100 字符 或 包含嵌套子标签。避免提取 `<div>hi</div>` 这类微观片段。

### 3.4 代码块保护

先扫描 ` ``` ` 标记的区间，区间内的 HTML 标签永不触发提取。

### 3.5 流式渲染

- 冻结段（已闭合）：执行完整 HTML 检测和分段
- 末尾未闭合段：不走 HTML 检测，保持现有 markdown 渲染
- 消息完成后自动切换为完整检测模式

---

## 4. HtmlPreview 改造

### 4.1 新增 prop

```
showToggle: Boolean (default: true)
```

| showToggle | 行为 |
|-----------|------|
| `true` | 现有行为：代码/预览切换栏 + 复制按钮，默认代码视图 |
| `false` | 无工具栏，直接 iframe 预览，初始 300px，postMessage 自适应 |

### 4.2 两条渲染路径

| | ````html` 代码块 | 自动检测 HTML |
|---|---|---|
| 触发 | markdown-it fence renderer | useMarkdown 预扫描 |
| showToggle | `true` | `false` |
| 挂载 | 动态 mount（MessageBubble） | 静态 `<HtmlPreview>` 声明 |
| 数据传递 | `data-html-code` base64 → prop | `:code` prop 直接传递 |

### 4.3 安全性（不变）

iframe sandbox 保持 `allow-scripts` 仅允许脚本执行，不添加 `allow-same-origin`/`allow-forms`/`allow-popups`/`allow-top-navigation`。

---

## 5. MessageBubble 渲染逻辑

```html
<!-- text block -->
<div v-html="block.html" />

<!-- html block (auto-detected, showToggle=false) -->
<HtmlPreview :code="block.code" :showToggle="false" />

<!-- html block (existing ```html, showToggle=true, dynamic mount) -->
<div class="html-preview-container" data-html-code="...">
  <!-- HtmlPreview mounted by mountHtmlPreviews() -->
</div>
```

---

## 6. 错误边界 & 边缘情况

| 场景 | 处理 |
|------|------|
| HTML 片段跨代码块边界 | 代码块区间外的才检测，不误拆 |
| 空内容 / 纯空白 | `detectHtmlType("") → "none"` |
| 超长 HTML（>500KB） | Blob URL 渲染（现有 >100KB 逻辑） |
| HTML 在消息中间 | text → html → text 序列 |
| 多个 HTML 片段 | 顺序产出多个独立 html block |
| 不完整 HTML（流中断） | 完成后再补检测 |
| HTML 含中文/Emoji | TextEncoder → Base64（UTF-8 安全） |
| 编辑模式 | 不做 HTML 检测，始终显示 textarea |

### 6.1 降级

- 检测异常 → fallback `"none"`，走 markdown
- 片段提取失败 → 不提取，内容保持 markdown
- iframe 加载失败 → 空白区域静默，不影响页面

---

## 7. 非目标

- 不修改后端 API
- 不修改 chat store
- 不给 ````html` 代码块加自动检测
- 不处理非 HTML 的 web 内容（SVG/WebGL/Canvas 等）
- 不添加 HTML 编辑功能
