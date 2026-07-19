# Markdown 流式渲染 + 代码高亮 + 复制按钮 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** AI 回复实时渲染 Markdown，代码块语法高亮（GitHub 风格）+ 复制按钮。

**Architecture:** `useMarkdown.js` composable 封装分段算法和 markdown-it 实例（含 fence renderer 注入复制按钮、DOMPurify 清洗、highlightAuto 保护），`MessageBubble.vue` 消费 computed 属性用 v-html 渲染冻结段+末尾段，事件委托处理复制交互。

**Tech Stack:** Vue 3 Composition API, markdown-it ^14.0.0, highlight.js ^11.9.0, dompurify ^3.0

## Global Constraints

- DOMPurify 清洗所有 markdown-it HTML 输出
- 代码块未闭合时跳过 markdown-it 渲染，转义为 `<pre>`
- `highlightAuto` 仅在 code.length ≤ 1000 且语言可识别时调用
- 复制按钮通过 `renderer.rules.fence` 注入，事件委托在硬编码 `.bubble-text` 容器上
- 分段过滤空段落，`:key="index"`（冻结段仅末尾追加）
- 现有 39 个后端测试必须通过

---

### Task 1: 安装依赖

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: npm install**

```bash
cd frontend && npm install markdown-it@^14.0.0 highlight.js@^11.9.0 dompurify@^3.0
```

- [ ] **Step 2: 验证安装**

```bash
cd frontend && node -e "require('markdown-it'); require('highlight.js'); require('dompurify'); console.log('OK')"
```
预期：`OK`

---

### Task 2: 创建 useMarkdown.js composable

**Files:**
- Create: `frontend/src/composables/useMarkdown.js`

**Interfaces:**
- Produces: `useMarkdown()` → `{ frozenHtmls: Ref<string[]>, liveHtml: Ref<string> }`
- 内部消费 `message.content`（通过 composable 参数或 watch）

- [ ] **Step 1: 创建 composeable 骨架**

```js
// frontend/src/composables/useMarkdown.js
import { ref, computed, watch } from 'vue';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import DOMPurify from 'dompurify';

// ── markdown-it 实例 ────────────────────────────

function highlightCode(code, lang) {
  if (lang && hljs.getLanguage(lang)) {
    return hljs.highlight(code, { language: lang }).value;
  }
  // P0: highlightAuto 性能保护
  if (!lang || code.length > 1000) {
    return md.utils.escapeHtml(code);
  }
  return hljs.highlightAuto(code).value;
}

const md = new MarkdownIt({
  html: false,
  breaks: true,
});

// ── P0: fence renderer 注入复制按钮 ──────────────

md.renderer.rules.fence = function (tokens, idx, options, env, self) {
  const token = tokens[idx];
  const lang = token.info.trim();
  const code = token.content;
  const highlighted = highlightCode(code, lang);

  return `<div class="code-block-wrapper">`
    + `<pre><code class="hljs${lang ? ' language-' + lang : ''}">${highlighted}</code></pre>`
    + `<button class="copy-btn" title="复制代码">`
    +   `<svg class="copy-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>`
    +   `<svg class="check-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" style="display:none"><polyline points="20 6 9 17 4 12"/></svg>`
    + `</button>`
    + `</div>`;
};

// ── 分段算法 ─────────────────────────────────────

function splitParagraphs(content) {
  const paragraphs = [];
  let current = '';
  let inCodeBlock = false;

  const lines = content.split('\n');
  for (const line of lines) {
    if (line.trimStart().startsWith('```')) {
      inCodeBlock = !inCodeBlock;
      current += line + '\n';
      continue;
    }
    if (inCodeBlock) {
      current += line + '\n';
      continue;
    }
    if (line.trim() === '') {
      if (current.trim() !== '') {
        paragraphs.push(current);
        current = '';
      }
    } else {
      current += line + '\n';
    }
  }
  if (current.trim() !== '') {
    paragraphs.push(current);
  }
  return paragraphs;
}

// ── 渲染函数 ─────────────────────────────────────

function safeRender(text) {
  return DOMPurify.sanitize(md.render(text));
}

function renderLive(content, inCodeBlock) {
  if (inCodeBlock) {
    const escaped = md.utils.escapeHtml(content);
    return `<pre class="hljs"><code>${escaped}</code></pre>`;
  }
  return safeRender(content);
}

function isInCodeBlock(content) {
  const matches = content.match(/^```/gm) || [];
  return matches.length % 2 === 1;
}

// ── composable ───────────────────────────────────

export function useMarkdown(contentRef) {
  const frozenHtmls = ref([]);
  const liveHtml = ref('');

  watch(
    () => contentRef.value,
    (content) => {
      if (!content) {
        frozenHtmls.value = [];
        liveHtml.value = '';
        return;
      }
      const paragraphs = splitParagraphs(content);
      if (paragraphs.length === 0) {
        frozenHtmls.value = [];
        liveHtml.value = '';
        return;
      }

      // 冻结段：前面已闭合的段落
      const frozen = paragraphs.slice(0, -1);
      frozenHtmls.value = frozen.map(p => safeRender(p));

      // 末尾段
      const last = paragraphs[paragraphs.length - 1];
      const inBlock = isInCodeBlock(last);
      liveHtml.value = renderLive(last, inBlock);
    },
    { immediate: true }
  );

  return { frozenHtmls, liveHtml };
}
```

- [ ] **Step 2: 前端构建验证**

```bash
cd frontend && npx vite build
```
预期：BUILD PASS

---

### Task 3: 改造 MessageBubble.vue

**Files:**
- Modify: `frontend/src/components/MessageBubble.vue`

- [ ] **Step 1: 重写模板部分**

将 `{{ message.content }}` 替换为 v-html 冻结段 + 末尾段结构，添加事件委托：

```vue
<template>
  <div class="bubble-row" :class="message.role">
    <div class="bubble">
      <div
        v-if="message.role === 'assistant' && message.reasoning_content"
        class="reasoning-block"
      >
        <div class="reasoning-header" @click="reasoningOpen = !reasoningOpen">
          <span class="reasoning-icon">{{ reasoningOpen ? '▼' : '▶' }}</span>
          <span>思考过程</span>
        </div>
        <div v-show="reasoningOpen" class="reasoning-content">
          {{ message.reasoning_content }}
        </div>
      </div>
      <div
        v-if="message.role === 'assistant'"
        class="bubble-text"
        @click="onBubbleClick"
      >
        <div
          v-for="(html, index) in frozenHtmls"
          :key="index"
          v-html="html"
        />
        <div v-html="liveHtml" />
      </div>
      <div v-else class="bubble-text">{{ message.content }}</div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: 重写 script setup**

```vue
<script setup>
import { ref, computed } from "vue";
import { useMarkdown } from "@/composables/useMarkdown.js";

const props = defineProps({
  message: { type: Object, required: true },
});

const reasoningOpen = ref(true);

const content = computed(() => props.message.content);
const { frozenHtmls, liveHtml } = useMarkdown(content);

function onBubbleClick(event) {
  const btn = event.target.closest('.copy-btn');
  if (!btn) return;

  const wrapper = btn.closest('.code-block-wrapper');
  const code = wrapper.querySelector('code').textContent;

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

- [ ] **Step 3: 更新样式**

在 `<style scoped>` 末尾追加代码块和复制按钮样式：

```css
/* ── 代码块 ───────────────────────────────────── */

.bubble-text :deep(.code-block-wrapper) {
  position: relative;
  margin: 8px 0;
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

/* ── 复制按钮 ─────────────────────────────────── */

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

/* ── 通用 v-html 内容样式 ─────────────────────── */

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
```

原有的 `.bubble-text` 样式 `white-space: pre-wrap` 需要移除（Markdown 渲染后不需要）。

- [ ] **Step 4: 移除 white-space: pre-wrap**

将：
```css
.bubble-text {
  white-space: pre-wrap;
  word-break: break-word;
}
```
改为：
```css
.bubble-text {
  word-break: break-word;
}
```

- [ ] **Step 5: 构建验证**

```bash
cd frontend && npx vite build
```
预期：BUILD PASS

---

### Task 4: 引入 highlight.js 主题

**Files:**
- Modify: `frontend/src/main.js`

- [ ] **Step 1: 添加 CSS import**

在 `frontend/src/main.js` 顶部添加：

```js
import 'highlight.js/styles/github.css';
```

- [ ] **Step 2: 构建验证**

```bash
cd frontend && npx vite build
```
预期：BUILD PASS，dist 中包含 GitHub 主题 CSS

---

### Task 5: 后端测试回归

- [ ] **Step 1: 运行全部后端测试**

```bash
cd backend && python -m pytest -v
```
预期：39 passed

---

### Task 6: 提交

- [ ] **Step 1: 提交**

```bash
git add frontend/package.json frontend/package-lock.json \
        frontend/src/composables/useMarkdown.js \
        frontend/src/components/MessageBubble.vue \
        frontend/src/main.js
git commit -m "feat: Markdown 流式渲染 + 代码高亮 + 复制按钮"
```
