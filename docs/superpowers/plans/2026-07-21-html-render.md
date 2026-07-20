# HTML 代码渲染 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为聊天应用添加 HTML 代码渲染：内联 HTML 标签直通 + HTML 代码块行内预览切换

**Architecture:** 修改 `useMarkdown.js` 开启 `html: true` 并在 fence renderer 中为 HTML 代码块输出占位容器；新增 `HtmlPreview.vue` 组件自管理 code↔preview 切换；`MessageBubble.vue` 负责在 DOM 渲染后将 HtmlPreview 动态挂载到占位容器上

**Tech Stack:** Vue 3 (composition API, `createApp` 动态挂载), markdown-it, DOMPurify, highlight.js, sandbox iframe

## Global Constraints

- DOMPurify 默认白名单用于内联 HTML 安全过滤
- 代码块预览使用 `sandbox="allow-scripts"` 的 iframe（不设 `allow-same-origin`）
- HTML 代码原始内容通过 Base64 编码存储在 `data-html-code` 属性中
- 非 HTML 代码块行为完全不受影响

---

### 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `frontend/src/composables/useMarkdown.js` | 修改 | `html: true`；fence renderer 检测 HTML lang 输出占位容器 |
| `frontend/src/components/HtmlPreview.vue` | **新增** | code↔preview 切换组件，sandbox iframe，自管理复制 |
| `frontend/src/components/MessageBubble.vue` | 修改 | 动态挂载/卸载 HtmlPreview，事件委托扩展 |

---

### Task 1: useMarkdown.js — 开启内联 HTML 直通

**Files:**
- Modify: `frontend/src/composables/useMarkdown.js:19`

**Interfaces:**
- Produces: markdown-it 实例 `md` 现配置 `html: true`，内联 HTML 标签通过 markdown-it 渲染

- [ ] **Step 1: 修改 html 配置**

将 `html: false` 改为 `html: true`。DOMPurify 在 `safeRender()` 中已经对 markdown-it 输出做清洗，开启 `html: true` 后安全标签通过、危险标签被 strip。

```js
// frontend/src/composables/useMarkdown.js 第 20 行

// 改前：
const md = new MarkdownIt({
  html: false,
  breaks: true,
});

// 改后：
const md = new MarkdownIt({
  html: true,
  breaks: true,
});
```

- [ ] **Step 2: 验证并提交**

```bash
cd frontend && npm run dev
# 在聊天中输入包含内联 HTML 的 Markdown，确认 <div style="color:red"> 渲染为红色
# 确认 <script>alert(1)</script> 被 DOMPurify 去除
```

```bash
git add frontend/src/composables/useMarkdown.js
git commit -m "feat: enable inline HTML passthrough in markdown-it"
```

---

### Task 2: useMarkdown.js — Fence renderer 支持 HTML 代码块占位

**Files:**
- Modify: `frontend/src/composables/useMarkdown.js:8-39`

**Interfaces:**
- Consumes: `md` 实例 (from Task 1)
- Produces: HTML 语言代码块输出 `<div class="html-preview-container" data-html-code="BASE64">...</div>`，非 HTML 块行为不变

- [ ] **Step 1: 添加 Base64 编码辅助函数**

在 `highlightCode` 函数之后、fence renderer 之前添加：

```js
// ── Base64 编码（UTF-8 安全）────────────────────

function toBase64(str) {
  return btoa(unescape(encodeURIComponent(str)));
}
```

- [ ] **Step 2: 修改 fence renderer，检测 HTML 语言**

```js
// 替换现有的 md.renderer.rules.fence（第 26-39 行）

md.renderer.rules.fence = function (tokens, idx, options, env, self) {
  const token = tokens[idx];
  const lang = token.info.trim();
  const code = token.content;
  const highlighted = highlightCode(code, lang);

  const copyBtn = `<button class="copy-btn" title="复制代码">`
    + `<svg class="copy-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>`
    + `<svg class="check-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" style="display:none"><polyline points="20 6 9 17 4 12"/></svg>`
    + `</button>`;

  // HTML 代码块：包裹在 html-preview-container 中，供 HtmlPreview 挂载
  if (/^html\b/i.test(lang)) {
    return `<div class="html-preview-container" data-html-code="${toBase64(code)}">`
      + `<div class="code-block-wrapper">`
      +   `<pre><code class="hljs language-html">${highlighted}</code></pre>`
      +   copyBtn
      + `</div>`
      + `</div>`;
  }

  // 非 HTML 代码块：保持现有行为
  return `<div class="code-block-wrapper">`
    + `<pre><code class="hljs${lang ? ' language-' + lang : ''}">${highlighted}</code></pre>`
    + copyBtn
    + `</div>`;
};
```

> 说明：HTML 代码块保留 `.code-block-wrapper` 作为初始内容（挂载前可见），HtmlPreview 挂载后会替换 innerHTML。

- [ ] **Step 3: 验证并提交**

```bash
cd frontend && npm run dev
# 发送包含 ```html 代码块的消息，确认：
# 1. HTML 代码块被包裹在 html-preview-container 中（浏览器检查元素）
# 2. data-html-code 属性包含 Base64 编码的原始代码
# 3. 非 HTML 代码块不受影响
```

```bash
git add frontend/src/composables/useMarkdown.js
git commit -m "feat: add HTML code block placeholder in fence renderer"
```

---

### Task 3: HtmlPreview.vue — 创建预览切换组件

**Files:**
- Create: `frontend/src/components/HtmlPreview.vue`

**Interfaces:**
- Consumes: `code: string` prop（已解码的原始 HTML，由 MessageBubble 从 `data-html-code` 读取并 Base64 解码后传入）
- Produces: 自包含的 code↔preview 切换 UI，无 emit

- [ ] **Step 1: 编写组件**

```vue
<!-- frontend/src/components/HtmlPreview.vue -->
<template>
  <div class="html-preview-block">
    <div class="preview-toolbar">
      <button
        :class="{ active: mode === 'code' }"
        @click="mode = 'code'"
        title="查看代码"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
        <span>代码</span>
      </button>
      <button
        :class="{ active: mode === 'preview' }"
        @click="mode = 'preview'"
        title="预览效果"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
        <span>预览</span>
      </button>
      <button class="copy-btn" title="复制代码" @click="onCopy">
        <svg class="copy-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
        <svg class="check-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" style="display:none"><polyline points="20 6 9 17 4 12"/></svg>
      </button>
    </div>

    <!-- 代码视图 -->
    <div v-show="mode === 'code'" class="code-view">
      <pre><code class="hljs language-html" v-html="highlightedHtml" />
    </div>

    <!-- 预览视图 -->
    <div v-show="mode === 'preview'" class="preview-view">
      <iframe
        ref="previewFrame"
        sandbox="allow-scripts"
        :srcdoc="srcdocContent"
        class="preview-frame"
        @load="onFrameLoad"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue';
import hljs from 'highlight.js';

const props = defineProps({
  code: { type: String, required: true },
});

const mode = ref('code');
const previewFrame = ref(null);
const frameHeight = ref('300px');

// ── Blob URL 生命周期管理 ───────────────────────

const blobUrl = ref(null);

function createBlobUrl(raw) {
  const blob = new Blob([raw], { type: 'text/html' });
  return URL.createObjectURL(blob);
}

function revokeBlobUrl() {
  if (blobUrl.value) {
    URL.revokeObjectURL(blobUrl.value);
    blobUrl.value = null;
  }
}

// 超长 HTML (>100KB) 用 blob: URL 替代直接 srcdoc
const srcdocContent = computed(() => {
  const raw = props.code;
  if (raw.length > 100 * 1024) {
    revokeBlobUrl();               // 先释放旧 URL
    blobUrl.value = createBlobUrl(raw);
    return blobUrl.value;
  }
  return raw;
});

// props.code 变化时释放旧 blob URL（确保非超长→超长切换时也清理）
watch(() => props.code, () => {
  // srcdocContent 已处理超长情况；若切回短文本则清理残留
  if (props.code && props.code.length <= 100 * 1024) {
    revokeBlobUrl();
  }
});

// ── 代码高亮 ─────────────────────────────────────

const highlightedHtml = computed(() => {
  if (!props.code) return '';
  try {
    return hljs.highlight(props.code, { language: 'html' }).value;
  } catch {
    return hljs.escapeHtml ? hljs.escapeHtml(props.code) : props.code;
  }
});

// ── iframe 高度自适应 ────────────────────────────

let observer = null;

function updateFrameHeight() {
  try {
    const body = previewFrame.value?.contentDocument?.body;
    if (body) {
      frameHeight.value = Math.max(body.scrollHeight, 100) + 'px';
    }
  } catch {
    // 忽略跨域限制
  }
}

function onFrameLoad() {
  if (!previewFrame.value) return;

  // 清理旧的 observer
  if (observer) observer.disconnect();

  try {
    const body = previewFrame.value.contentDocument?.body;
    if (body) {
      updateFrameHeight();

      // MutationObserver 监听内容动态变化（JS 添加元素、展开折叠等）
      observer = new MutationObserver(() => {
        updateFrameHeight();
      });
      observer.observe(body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['style', 'class'],
      });
    }
  } catch {
    // 忽略
  }
}

// ── 复制 ─────────────────────────────────────────

function onCopy() {
  navigator.clipboard.writeText(props.code).then(() => {
    const btn = event.currentTarget;
    btn.querySelector('.copy-icon').style.display = 'none';
    btn.querySelector('.check-icon').style.display = '';
    setTimeout(() => {
      btn.querySelector('.copy-icon').style.display = '';
      btn.querySelector('.check-icon').style.display = 'none';
    }, 2000);
  });
}

// ── 清理 ─────────────────────────────────────────

onBeforeUnmount(() => {
  revokeBlobUrl();
  if (observer) observer.disconnect();
});
</script>

<style scoped>
.html-preview-block {
  margin: 8px 0;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  overflow: hidden;
}

.preview-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 8px;
  background: #f6f8fa;
  border-bottom: 1px solid #d0d7de;
}

.preview-toolbar button {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid transparent;
  border-radius: 4px;
  background: transparent;
  color: #656d76;
  cursor: pointer;
  font-size: 12px;
  line-height: 1;
}

.preview-toolbar button:hover {
  background: #eaeef2;
}

.preview-toolbar button.active {
  background: #fff;
  border-color: #d0d7de;
  color: #24292f;
}

.preview-toolbar .copy-btn {
  margin-left: auto;
}

.code-view pre {
  margin: 0;
  padding: 12px 16px;
  background: #f6f8fa;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.5;
}

.code-view code {
  background: transparent;
  padding: 0;
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
}

.preview-view {
  background: #fff;
}

.preview-frame {
  width: 100%;
  height: v-bind(frameHeight);
  border: none;
  display: block;
}
</style>
```

- [ ] **Step 2: 验证组件可独立使用**

由于没有单元测试框架，通过手动验证：后续 Task 4 挂载后整体验证。此处先确保语法正确：

```bash
cd frontend && npx vite build --mode development 2>&1 | head -20
# 确认无编译错误
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/HtmlPreview.vue
git commit -m "feat: add HtmlPreview component with code/preview toggle"
```

---

### Task 4: MessageBubble.vue — 动态挂载 HtmlPreview

**Files:**
- Modify: `frontend/src/components/MessageBubble.vue`

**Interfaces:**
- Consumes: `HtmlPreview` 组件 (from Task 3), `.html-preview-container` DOM 元素 (from Task 2 fence renderer)
- Produces: HTML 代码块具备预览能力，非 HTML 块不变

- [ ] **Step 1: 修改 script setup — 添加动态挂载逻辑**

```vue
<!-- 替换 script setup 部分 -->

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick, createApp } from "vue";
import { useMarkdown } from "@/composables/useMarkdown.js";
import HtmlPreview from "@/components/HtmlPreview.vue";

const props = defineProps({
  message: { type: Object, required: true },
});

const reasoningOpen = ref(true);

const content = computed(() => props.message.content);
const { frozenHtmls, liveHtml } = useMarkdown(content);

// ── HtmlPreview 动态挂载 ────────────────────────

const bubbleTextRef = ref(null);
const previewApps = new Map();  // DOM element → Vue app

function mountHtmlPreviews() {
  if (!bubbleTextRef.value) return;

  const containers = bubbleTextRef.value.querySelectorAll('.html-preview-container');
  containers.forEach(container => {
    if (previewApps.has(container)) return;  // 已挂载

    const base64 = container.getAttribute('data-html-code');
    if (!base64) return;

    let code;
    try {
      code = decodeURIComponent(escape(atob(base64)));
    } catch {
      code = '';
    }

    const app = createApp(HtmlPreview, { code });
    app.mount(container);
    previewApps.set(container, app);
  });
}

function unmountHtmlPreviews() {
  previewApps.forEach((app, container) => {
    app.unmount();
  });
  previewApps.clear();
}

// 渲染后挂载
watch([frozenHtmls, liveHtml], () => {
  unmountHtmlPreviews();
  nextTick(() => mountHtmlPreviews());
});

onMounted(() => {
  nextTick(() => mountHtmlPreviews());
});

onBeforeUnmount(() => {
  unmountHtmlPreviews();
});

// ── 事件委托：仅处理非 HTML 代码块的复制 ─────────

function onBubbleClick(event) {
  const btn = event.target.closest('.copy-btn');
  if (!btn) return;

  // 跳过 HtmlPreview 内部的复制按钮（组件自管理）
  if (btn.closest('.html-preview-block')) return;

  const wrapper = btn.closest('.code-block-wrapper');
  if (!wrapper) return;

  const code = wrapper.querySelector('code')?.textContent || '';

  navigator.clipboard.writeText(code).then(() => {
    btn.querySelector('.copy-icon').style.display = 'none';
    btn.querySelector('.check-icon').style.display = '';
    setTimeout(() => {
      btn.querySelector('.copy-icon').style.display = '';
      btn.querySelector('.check-icon').style.display = 'none';
    }, 2000);
  });
}
</script>
```

- [ ] **Step 2: 修改 template — 添加 ref**

在 `.bubble-text` 上添加 `ref="bubbleTextRef"`：

```vue
<!-- 改前： -->
<div
  v-if="message.role === 'assistant'"
  class="bubble-text"
  @click="onBubbleClick"
>

<!-- 改后： -->
<div
  v-if="message.role === 'assistant'"
  ref="bubbleTextRef"
  class="bubble-text"
  @click="onBubbleClick"
>
```

- [ ] **Step 3: 添加 HtmlPreview 相关 CSS**

在 `<style scoped>` 末尾添加：

```css
/* ── HtmlPreview 容器 ──────────────────────────── */

.bubble-text :deep(.html-preview-container) {
  margin: 8px 0;
}
```

- [ ] **Step 4: 验证并提交**

```bash
cd frontend && npm run dev
# 测试场景：
# 1. 发送 ```html <h1>Hello</h1> ``` — 确认出现预览按钮，点击切换为渲染视图
# 2. 发送 ```js console.log(1) ``` — 确认无预览按钮，复制正常
# 3. 发送多个 HTML 代码块 — 各自独立切换
# 4. 流式输出 — 代码块闭合后预览按钮才出现
# 5. 复制按钮在预览工具栏和代码块上都可用
```

```bash
git add frontend/src/components/MessageBubble.vue
git commit -m "feat: dynamically mount HtmlPreview on HTML code blocks"
```

---

### Task 5: 集成验证与收尾

**Files:**
- 无新增文件，验证整体功能

- [ ] **Step 1: 完整场景验证**

启动应用：

```bash
cd frontend && npm run dev
```

逐项验证：

| # | 场景 | 预期结果 |
|---|------|----------|
| 1 | MD 含 `<div style="color:red">红色</div>` | 文字显示为红色 |
| 2 | MD 含 `<script>alert(1)</script>` | script 标签被去除，不弹窗 |
| 3 | ` ```html <h1>Title</h1> ``` ` | 代码块有「代码/预览」切换按钮，预览显示大标题 |
| 4 | ` ```javascript console.log(1) ``` ` | 无预览按钮，只有复制按钮 |
| 5 | 同一消息中 2 个 ` ```html ` 块 | 各自独立切换，互不影响 |
| 6 | 流式输出 HTML 代码块 | 闭合前不显示，闭合后立即出现预览按钮 |
| 7 | 预览模式下点复制 | 复制原始 HTML 代码 |
| 8 | 消息重新生成 | 旧预览实例正确清理，新内容正常渲染 |

- [ ] **Step 2: 修复发现的问题并提交**

```bash
# 如有修复：
git add -A && git commit -m "fix: integration fixes for HTML render feature"
```
