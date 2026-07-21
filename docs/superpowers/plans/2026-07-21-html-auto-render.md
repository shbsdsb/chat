# 自动 HTML 渲染支持 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** AI 回复中的 HTML（完整文档或片段）自动用 iframe 渲染，无需手动切换预览

**Architecture:** useMarkdown composable 新增 HTML 检测层，产出 `blocks` 数组 + `isCompleteHtml` 标志；MessageBubble 按 block 类型分流渲染（text → v-html，html → HtmlPreview）；HtmlPreview 新增 `showToggle` prop 控制工具栏显隐

**Tech Stack:** Vue 3 Composition API, markdown-it, DOMPurify, highlight.js

## Global Constraints

- 不改动后端 API、chat store、router
- 现有 ````html` 代码块（代码/预览切换）行为完全不变
- 流式渲染中仅冻结段走 HTML 检测，末尾未闭合段保持 markdown 渲染
- iframe sandbox 仅 `allow-scripts`，不添加 `allow-same-origin`
- 不小于 100 字符且无嵌套的 HTML 片段不触发提取

---

### Task 1: HtmlPreview — 添加 showToggle prop

**Files:**
- Modify: `frontend/src/components/HtmlPreview.vue`

**Interfaces:**
- Produces: prop `showToggle: Boolean (default: true)` — false 时隐藏工具栏，默认显示 iframe 预览

- [ ] **Step 1: 添加 showToggle prop 和默认预览模式**

替换 `<script setup>` 中的 props 定义：

```javascript
const props = defineProps({
  code: { type: String, required: true },
  showToggle: { type: Boolean, default: true },
});
```

替换 mode 初始化为根据 showToggle 决定：

```javascript
const mode = ref(props.showToggle ? 'code' : 'preview');
```

- [ ] **Step 2: 条件渲染预览工具栏**

替换 `<template>` 中工具栏部分，用 `v-if="showToggle"` 包裹整个 `.preview-toolbar`：

```html
<div v-if="showToggle" class="preview-toolbar">
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
```

- [ ] **Step 3: 验证构建**

```bash
cd frontend && npm run build 2>&1 | tail -5
```

预期: `✓ built in ...` 无报错。

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/HtmlPreview.vue
git commit -m "feat: add showToggle prop to HtmlPreview for toolbar-less rendering"
```

---

### Task 2: useMarkdown — 添加 HTML 检测函数

**Files:**
- Modify: `frontend/src/composables/useMarkdown.js`

**Interfaces:**
- Produces: `detectHtmlType(content)` → `"full" | "mixed" | "none"`
- Produces: `getCodeBlockRanges(content)` → `[{start, end}, ...]`
- Produces: `isInsideCodeBlock(pos, ranges)` → `Boolean`

- [ ] **Step 1: 在文件末尾（export function useMarkdown 之前）添加三个辅助函数**

```javascript
// ── HTML 检测 ──────────────────────────────────

const BLOCK_TAGS = new Set([
  'div', 'section', 'article', 'header', 'footer', 'nav', 'main', 'aside',
  'table', 'form', 'fieldset', 'details', 'figure', 'ul', 'ol', 'dl'
]);

function getCodeBlockRanges(content) {
  const ranges = [];
  const re = /^```/gm;
  let match;
  while ((match = re.exec(content)) !== null) {
    if (ranges.length > 0 && ranges[ranges.length - 1].end === undefined) {
      ranges[ranges.length - 1].end = match.index;
    } else {
      ranges.push({ start: match.index });
    }
  }
  if (ranges.length > 0 && ranges[ranges.length - 1].end === undefined) {
    ranges[ranges.length - 1].end = content.length;
  }
  return ranges;
}

function isInsideCodeBlock(pos, ranges) {
  return ranges.some(r => pos >= r.start && pos < r.end);
}

function detectHtmlType(content) {
  const trimmed = content.trim();
  if (!trimmed) return 'none';
  if (/^<!DOCTYPE\s+html/i.test(trimmed) || /^<html[\s>]/i.test(trimmed)) {
    return 'full';
  }
  const fragments = extractHtmlFragments(content);
  return fragments.length > 0 ? 'mixed' : 'none';
}
```

- [ ] **Step 2: 验证构建**

```bash
cd frontend && npm run build 2>&1 | tail -5
```

预期: `✓ built in ...` 无报错（`extractHtmlFragments` 尚未定义，但 `detectHtmlType` 尚未被调用，构建不会报引用错误——如果报错则先注释掉 `detectHtmlType` 内的 `extractHtmlFragments` 调用）。

- [ ] **Step 3: 提交**

```bash
git add frontend/src/composables/useMarkdown.js
git commit -m "feat: add detectHtmlType and code block range helpers"
```

---

### Task 3: useMarkdown — 添加 HTML 片段提取函数

**Files:**
- Modify: `frontend/src/composables/useMarkdown.js`

**Interfaces:**
- Produces: `extractHtmlFragments(content)` → `[{start, end, code}, ...]`
- Produces: `splitMixed(content)` → `[{type, content|code}, ...]`

- [ ] **Step 1: 在 detectHtmlType 之前添加 extractHtmlFragments**

```javascript
function extractHtmlFragments(content) {
  const codeBlockRanges = getCodeBlockRanges(content);
  const fragments = [];
  const tagPattern = /<(div|section|article|header|footer|nav|main|aside|table|form|fieldset|details|figure|ul|ol|dl)(\s[^>]*)?>/gi;

  let match;
  while ((match = tagPattern.exec(content)) !== null) {
    const tagName = match[1].toLowerCase();
    if (isInsideCodeBlock(match.index, codeBlockRanges)) continue;

    const openTagLen = match[0].length;

    // 用深度计数找匹配的闭合标签
    let depth = 1;
    let searchPos = match.index + openTagLen;
    const tagRe = new RegExp(`<\\/?${tagName}[\\s>]`, 'gi');
    tagRe.lastIndex = searchPos;

    let closeMatchEnd = -1;
    let innerMatch;
    while ((innerMatch = tagRe.exec(content)) !== null) {
      if (isInsideCodeBlock(innerMatch.index, codeBlockRanges)) continue;
      if (content[innerMatch.index + 1] === '/') {
        depth--;
        if (depth === 0) {
          const gt = content.indexOf('>', innerMatch.index);
          closeMatchEnd = gt !== -1 ? gt + 1 : innerMatch.index + innerMatch[0].length;
          break;
        }
      } else {
        depth++;
      }
    }

    if (closeMatchEnd === -1) continue;

    const htmlCode = content.slice(match.index, closeMatchEnd);

    // 质量门槛：≥ 100 字符 或 包含嵌套子标签
    if (htmlCode.length < 100) {
      const inner = htmlCode.slice(openTagLen, htmlCode.length - (closeMatchEnd - innerMatch.index));
      if (!/<(\w+)[\s>]/i.test(inner)) continue;
    }

    fragments.push({ start: match.index, end: closeMatchEnd, code: htmlCode });
  }

  // 排序并移除重叠片段
  fragments.sort((a, b) => a.start - b.start);
  const filtered = [];
  let lastEnd = 0;
  for (const f of fragments) {
    if (f.start >= lastEnd) {
      filtered.push(f);
      lastEnd = f.end;
    }
  }
  return filtered;
}
```

- [ ] **Step 2: 在 extractHtmlFragments 之后添加 splitMixed**

```javascript
function splitMixed(content) {
  const fragments = extractHtmlFragments(content);
  if (fragments.length === 0) {
    return [{ type: 'text', content }];
  }

  const blocks = [];
  let pos = 0;
  for (const frag of fragments) {
    if (frag.start > pos) {
      blocks.push({ type: 'text', content: content.slice(pos, frag.start) });
    }
    blocks.push({ type: 'html', code: frag.code });
    pos = frag.end;
  }
  if (pos < content.length) {
    blocks.push({ type: 'text', content: content.slice(pos) });
  }
  return blocks;
}
```

- [ ] **Step 3: 验证构建**

```bash
cd frontend && npm run build 2>&1 | tail -5
```

预期: `✓ built in ...`

- [ ] **Step 4: 提交**

```bash
git add frontend/src/composables/useMarkdown.js
git commit -m "feat: add extractHtmlFragments and splitMixed for HTML detection"
```

---

### Task 4: useMarkdown — 集成 HTML 检测到 composable

**Files:**
- Modify: `frontend/src/composables/useMarkdown.js`

**Interfaces:**
- Modifies: `useMarkdown(contentRef)` 返回值新增 `blocks`（ref）和 `isCompleteHtml`（ref）

- [ ] **Step 1: 修改 useMarkdown 函数，新增 blocks 和 isCompleteHtml，修改 watch 回调**

完整替换 `useMarkdown` 函数：

```javascript
export function useMarkdown(contentRef) {
  const frozenHtmls = ref([]);
  const liveHtml = ref('');
  const blocks = ref([]);
  const isCompleteHtml = ref(false);

  watch(
    () => contentRef.value,
    (content) => {
      if (!content) {
        frozenHtmls.value = [];
        liveHtml.value = '';
        blocks.value = [];
        isCompleteHtml.value = false;
        return;
      }

      const htmlType = detectHtmlType(content);

      // ── 完整 HTML 文档 ──
      if (htmlType === 'full') {
        frozenHtmls.value = [];
        liveHtml.value = '';
        blocks.value = [{ type: 'html', code: content }];
        isCompleteHtml.value = true;
        return;
      }

      isCompleteHtml.value = false;

      // ── 混合内容 ──
      if (htmlType === 'mixed') {
        const paragraphs = splitParagraphs(content);
        if (paragraphs.length === 0) {
          frozenHtmls.value = [];
          liveHtml.value = '';
          blocks.value = [];
          return;
        }

        // 冻结段走 HTML 检测和分段
        const frozenContent = paragraphs.slice(0, -1).join('\n\n');
        const liveContent = paragraphs[paragraphs.length - 1] || '';

        const mixedBlocks = splitMixed(frozenContent);
        // 将 text block 的 content 渲染为 markdown HTML
        const renderedBlocks = mixedBlocks.map(b => {
          if (b.type === 'text') {
            return { type: 'text', html: safeRender(b.content) };
          }
          return b;
        });

        blocks.value = renderedBlocks;
        frozenHtmls.value = [];
        liveHtml.value = renderLive(liveContent, isInCodeBlock(liveContent));
        return;
      }

      // ── 纯文本 ──
      blocks.value = [];

      const paragraphs = splitParagraphs(content);
      if (paragraphs.length === 0) {
        frozenHtmls.value = [];
        liveHtml.value = '';
        return;
      }

      const frozen = paragraphs.slice(0, -1);
      frozenHtmls.value = frozen.map(p => safeRender(p));

      const last = paragraphs[paragraphs.length - 1];
      liveHtml.value = renderLive(last, isInCodeBlock(last));
    },
    { immediate: true }
  );

  return { frozenHtmls, liveHtml, blocks, isCompleteHtml };
}
```

- [ ] **Step 2: 验证构建**

```bash
cd frontend && npm run build 2>&1 | tail -5
```

预期: `✓ built in ...`

- [ ] **Step 3: 提交**

```bash
git add frontend/src/composables/useMarkdown.js
git commit -m "feat: integrate HTML detection into useMarkdown composable"
```

---

### Task 5: MessageBubble — 按 block 类型条件渲染

**Files:**
- Modify: `frontend/src/components/MessageBubble.vue`

**Interfaces:**
- Consumes: `useMarkdown()` 新增的 `blocks` 和 `isCompleteHtml`

- [ ] **Step 1: 解构新增的返回值**

在 `<script setup>` 中修改 useMarkdown 的解构：

```javascript
const { frozenHtmls, liveHtml, blocks, isCompleteHtml } = useMarkdown(content);
```

- [ ] **Step 2: 修改模板 — 完整 HTML 文档渲染**

在 `.bubble-row` 开标签后、`.bubble` 之前插入完整 HTML 渲染路径：

```html
  <div class="bubble-row" :class="message.role">
    <!-- 完整 HTML 文档：整条消息用 HtmlPreview 渲染 -->
    <div v-if="isCompleteHtml && blocks.length === 1" class="bubble bubble-html" style="width:100%;padding:0">
      <HtmlPreview :code="blocks[0].code" :showToggle="false" />
    </div>
```

并将原有 `.bubble` 用 `v-else` 包裹：

```html
    <div v-else class="bubble" :class="{ 'bubble-editing': isEditing }">
```

- [ ] **Step 3: 修改模板 — 混合内容渲染**

在正常模式的 `<template v-else>` 内，在推理块之后、现有内容之前，添加 blocks 渲染逻辑：

```html
      <!-- 正常显示模式 -->
      <template v-else>
        <!-- 混合内容：HTML block + text block 交替 -->
        <template v-if="blocks.length > 0">
          <template v-for="block in blocks" :key="block.start || block.code?.slice(0,20)">
            <div v-if="block.type === 'text'" v-html="block.html" class="bubble-text" />
            <div v-else class="html-auto-block">
              <HtmlPreview :code="block.code" :showToggle="false" />
            </div>
          </template>
          <div v-if="liveHtml" v-html="liveHtml" class="bubble-text" />
        </template>
        <!-- 纯文本：现有渲染逻辑 -->
        <template v-else>
          <!-- ... 现有代码保持不变 ... -->
```

以下为需要修改的完整 template 结构（展示关键路径）：

```html
<template>
  <div class="bubble-row" :class="message.role">
    <!-- 编辑工具栏 -->
    <div v-if="isEditing" class="edit-toolbar">
      <button class="edit-btn save-btn" title="保存" @click="handleSave">✓</button>
      <button class="edit-btn cancel-btn" title="取消" @click="handleCancel">✗</button>
    </div>

    <!-- 完整 HTML 文档 -->
    <div v-if="isCompleteHtml && blocks.length === 1" class="bubble bubble-html" style="width:100%;padding:0">
      <HtmlPreview :code="blocks[0].code" :showToggle="false" />
    </div>

    <div v-else class="bubble" :class="{ 'bubble-editing': isEditing }">
      <!-- 编辑模式 -->
      <textarea
        v-if="isEditing"
        ref="editTextareaRef"
        v-model="editContent"
        class="edit-textarea"
        rows="6"
      />
      <!-- 正常显示模式 -->
      <template v-else>
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

        <!-- 混合 blocks 渲染 -->
        <template v-if="blocks.length > 0">
          <template v-for="(block, i) in blocks" :key="i">
            <div v-if="block.type === 'text'" v-html="block.html" class="bubble-text" />
            <div v-else class="html-auto-block">
              <HtmlPreview :code="block.code" :showToggle="false" />
            </div>
          </template>
          <div v-if="liveHtml" v-html="liveHtml" class="bubble-text" />
        </template>

        <!-- 纯文本：现有渲染 -->
        <template v-else>
          <div
            v-if="message.role === 'assistant'"
            ref="bubbleTextRef"
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
        </template>
      </template>
    </div>
  </div>
</template>
```

- [ ] **Step 4: 添加 .html-auto-block 的 CSS**

在 `<style scoped>` 末尾添加：

```css
.html-auto-block {
  margin: 8px 0;
}
```

- [ ] **Step 5: 验证构建**

```bash
cd frontend && npm run build 2>&1 | tail -5
```

预期: `✓ built in ...`

- [ ] **Step 6: 提交**

```bash
git add frontend/src/components/MessageBubble.vue
git commit -m "feat: render auto-detected HTML blocks in MessageBubble"
```

---

### Task 6: 端到端验证

**Files:**
- 无代码改动，手动验证

- [ ] **Step 1: 启动开发环境**

```bash
cd frontend && npm run dev &
```

- [ ] **Step 2: 验证场景 1 — 纯 Markdown 不受影响**

发送消息："你好，请用 **粗体** 和 `代码` 回复我"

预期: markdown 照常渲染，粗体和行内代码显示正常。

- [ ] **Step 3: 验证场景 2 — 完整 HTML 文档**

在 AI 回复中粘贴一份以 `<!DOCTYPE html>` 开头的 HTML 文档。

预期: 整条消息以 iframe 直接渲染 HTML，无 markdown 包裹，无工具栏。

- [ ] **Step 4: 验证场景 3 — HTML 片段嵌入文本**

发送消息触发 AI 输出类似："下面是卡片：\n<div class=\"card\"><h2>标题</h2><p>内容</p></div>\n上面是卡片"

预期: 文本部分 markdown 渲染，`<div>` 片段作为独立 iframe 渲染（无工具栏）。

- [ ] **Step 5: 验证场景 4 — ````html` 代码块不受影响**

在消息中手动输入或让 AI 输出 ````html` 代码块。

预期: 代码块照常有代码/预览工具栏，默认显示代码视图。

- [ ] **Step 6: 验证场景 5 — 流式渲染不崩溃**

在 AI 流式回复过程中观察。

预期: 流式过程正常，不卡顿；消息完成后 HTML 自动渲染。

- [ ] **Step 7: 提交（如有遗留文件）**

```bash
git status
# 如有未提交的改动，提交之
```
