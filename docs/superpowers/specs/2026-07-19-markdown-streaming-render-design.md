# Markdown 流式渲染 + 代码高亮 + 复制按钮

日期：2026-07-19

## 依赖

```
markdown-it  ^14.0.0   — MD 解析
highlight.js ^11.9.0   — 代码语法高亮，GitHub 主题
dompurify    ^3.0      — HTML 安全清洗
```

## 设计

### 1. 分段冻结渲染策略

按空行（`\n\n`）分隔段落，维护 `inCodeBlock` 状态确保代码块内不分割。已闭合段落一次性渲染并缓存，仅末尾段落实时更新。

**分段算法：**
```
paragraphs = []
current   = ""
inCodeBlock = false

遍历 content 每一行 line：
  ├─ line 以 ``` 开头（trim 后） → 翻转 inCodeBlock
  │    └─ current += line + "\n"
  ├─ inCodeBlock === true
  │    └─ current += line + "\n"         // 代码块内不分割
  └─ inCodeBlock === false
       ├─ line 为空（trim 后 ""）
       │    └─ if current.trim() !== ""  // P1: 过滤空段
       │         paragraphs.push(current)
       │         current = ""
       └─ line 非空
            └─ current += line + "\n"

最后 if current.trim() !== "" → paragraphs.push(current)
```

**渲染：**
- 冻结段（`paragraphs.slice(0, -1)`）：用 markdown-it 渲染 → DOMPurify 清洗 → `v-html` 缓存，永不更新
- 末尾段（`paragraphs[last]`）：根据 `inCodeBlock` 状态分两种路径渲染，随流式 content 变化自动更新

### 2. 代码块流式保护（P0）

末尾段渲染规则取决于它是否处于未闭合的代码块中：

| 状态 | 渲染方式 |
|------|---------|
| `inCodeBlock === false` | `md.render(content)` → `DOMPurify.sanitize()` |
| `inCodeBlock === true` | HTML 转义后用 `<pre class="hljs"><code>${escaped}</code></pre>` 包裹 |

当代码块未闭合时（只有开头 ``` 没有结尾 ```），markdown-it 会将后续内容误认为代码块，所以跳过 markdown-it 渲染，直接作为纯文本代码展示。

```js
function renderLive(content, inCodeBlock) {
  if (inCodeBlock) {
    const escaped = md.utils.escapeHtml(content);
    return `<pre class="hljs"><code>${escaped}</code></pre>`;
  }
  const html = md.render(content);
  return DOMPurify.sanitize(html);
}
```

### 3. 安全清洗（P0）

所有 markdown-it 输出在插入 DOM 前必须经过 DOMPurify 清洗：

```js
import DOMPurify from 'dompurify';

function safeRender(text) {
  return DOMPurify.sanitize(md.render(text));
}
```

- 冻结段：渲染时清洗一次
- 末尾段（inCodeBlock=false）：每次内容变化清洗一次

### 4. markdown-it 配置

```js
const md = new MarkdownIt({
  html: false,
  breaks: true,
});
```

**highlight 函数（P0：highlightAuto 性能保护）：**

```js
function highlightCode(code, lang) {
  if (lang && hljs.getLanguage(lang)) {
    return hljs.highlight(code, { language: lang }).value;
  }
  // 性能保护：长代码（>1000 字符）或无法识别语言 → 跳过 highlightAuto
  if (!lang || code.length > 1000) {
    return md.utils.escapeHtml(code);
  }
  return hljs.highlightAuto(code).value;
}
```

`highlightAuto` 会遍历所有已注册语言尝试匹配，长代码块开销巨大。超过 1000 字符直接回退到转义纯文本，避免阻塞主线程影响流式渲染帧率。

### 5. 复制按钮（P0：renderer.rules.fence 注入）

**注入方式** — 覆盖 markdown-it 的 `renderer.rules.fence`，在生成 HTML 时直接产生完整的 `<div> + <pre> + <button>` 结构，无需渲染后 DOM 操作。

```js
const defaultFence = md.renderer.rules.fence.bind(md.renderer.rules);

md.renderer.rules.fence = function (tokens, idx, options, env, self) {
  const token = tokens[idx];
  const lang = token.info.trim();
  const code = token.content;
  const highlighted = highlightCode(code, lang);

  return `
    <div class="code-block-wrapper">
      <pre><code class="hljs${lang ? ' language-' + lang : ''}">${highlighted}</code></pre>
      <button class="copy-btn" title="复制代码">
        <svg class="copy-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
        <svg class="check-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" style="display:none"><polyline points="20 6 9 17 4 12"/></svg>
      </button>
    </div>`;
};
```

**交互** — 在 MessageBubble 模板中硬编码的容器上使用事件委托，不受 v-html 内容重新生成影响：

```html
<!-- template 中硬编码，不是 v-html 动态生成的 -->
<div class="bubble-text" @click="onBubbleClick">
  <div v-for="..." v-html="..."></div>
</div>
```

```js
function onBubbleClick(event) {
  const btn = event.target.closest('.copy-btn');
  if (!btn) return;

  const wrapper = btn.closest('.code-block-wrapper');
  // P1: 通过硬编码父容器内的 querySelector 获取代码文本
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
```

**样式（GitHub 风格）：**
```css
.code-block-wrapper {
  position: relative;
  margin: 8px 0;
}
.code-block-wrapper pre {
  margin: 0;
  padding: 16px;
  border-radius: 6px;
  background: #f6f8fa;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.5;
}
.copy-btn {
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
}
.code-block-wrapper:hover .copy-btn {
  opacity: 1;
}
.copy-btn:hover {
  background: #f3f4f6;
}
```

### 6. 换行处理（P1）

- 分段时 `current.trim() !== ""` 才 push，过滤空段落，避免 `<p></p>` 堆积
- markdown-it 配置 `breaks: true`，单换行自动转 `<br>`

### 7. MessageBubble.vue 结构

**模板：**

```html
<div
  class="bubble-text"
  @click="onBubbleClick"
>
  <!-- 冻结段：仅在末尾追加，不在中间插入/删除 → index 作为 key 安全 -->
  <div
    v-for="(html, index) in frozenHtmls"
    :key="index"
    v-html="html"
  />
  <!-- 末尾段 -->
  <div v-html="liveHtml" />
</div>
```

**Key 策略：** `:key="index"`。冻结段列表仅在流式输入末尾追加新段，不会在中间插入或删除已有段落，因此用 index 作为 key 不会导致 DOM 复用错乱。历史消息重新加载时冻结段列表整体替换，旧的 key 全部失效重建，index 仍然正确。

**事件委托：** `.bubble-text` 是模板中硬编码的 `<div>`，不是 v-html 动态生成。即使 v-html 内容随流式输入不断重建，事件冒泡始终经过此固定容器，`.copy-btn` 点击能被稳定捕获。

推理内容（reasoning_content）保持纯文本 `{{ }}` 不变。

### 8. highlight.js 主题

CSS import：
```css
@import 'highlight.js/styles/github.css';
```
