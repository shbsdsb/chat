import { ref, watch } from 'vue';
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

// ── Base64 编码（UTF-8 安全）────────────────────

function toBase64(str) {
  const bytes = new TextEncoder().encode(str);
  const binStr = Array.from(bytes, b => String.fromCharCode(b)).join('');
  return btoa(binStr);
}

const md = new MarkdownIt({
  html: true,
  breaks: true,
});

// ── P0: fence renderer 注入复制按钮 ──────────────

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

// ── HTML 检测 ──────────────────────────────────

const BLOCK_TAGS = new Set([
  'div', 'section', 'article', 'header', 'footer', 'nav', 'main', 'aside',
  'table', 'form', 'fieldset', 'details', 'figure', 'ul', 'ol', 'dl'
]);

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

// ── composable ───────────────────────────────────

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
