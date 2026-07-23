import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import DOMPurify from 'dompurify';

// ── Base64 编码（UTF-8 安全）────────────────────
export function toBase64(str) {
  const bytes = new TextEncoder().encode(str);
  const binStr = Array.from(bytes, b => String.fromCharCode(b)).join('');
  return btoa(binStr);
}

// ── markdown-it 实例 ────────────────────────────
function highlightCode(code, lang) {
  if (lang && hljs.getLanguage(lang)) {
    return hljs.highlight(code, { language: lang }).value;
  }
  if (!lang || code.length > 1000) {
    return md.utils.escapeHtml(code);
  }
  return hljs.highlightAuto(code).value;
}

const md = new MarkdownIt({
  html: true,
  breaks: true,
});

// ── fence renderer 注入复制按钮 ──────────────
md.renderer.rules.fence = function (tokens, idx, options, env, self) {
  const token = tokens[idx];
  const lang = token.info.trim();
  const code = token.content;
  const highlighted = highlightCode(code, lang);

  const copyBtn = `<button class="copy-btn" title="复制代码">`
    + `<svg class="copy-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>`
    + `<svg class="check-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" style="display:none"><polyline points="20 6 9 17 4 12"/></svg>`
    + `</button>`;

  if (/^html\b/i.test(lang)) {
    return `<div class="html-preview-container" data-html-code="${toBase64(code)}">`
      + `<div class="code-block-wrapper">`
      +   `<pre><code class="hljs language-html">${highlighted}</code></pre>`
      +   copyBtn
      + `</div>`
      + `</div>`;
  }

  return `<div class="code-block-wrapper">`
    + `<pre><code class="hljs${lang ? ' language-' + lang : ''}">${highlighted}</code></pre>`
    + copyBtn
    + `</div>`;
};

// ── 渲染函数 ─────────────────────────────────────
export function safeRender(text) {
  return DOMPurify.sanitize(md.render(text));
}

export function renderLive(content, inCodeBlock) {
  if (inCodeBlock) {
    const escaped = md.utils.escapeHtml(content);
    return `<pre class="hljs"><code>${escaped}</code></pre>`;
  }
  return safeRender(content);
}

export function isInCodeBlock(content) {
  const matches = content.match(/^```/gm) || [];
  return matches.length % 2 === 1;
}
