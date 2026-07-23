import { getCodeBlockRanges, isInsideCodeBlock } from './splitter';

// ── HTML 检测 ──────────────────────────────────
const BLOCK_TAGS = new Set([
  'div', 'section', 'article', 'header', 'footer', 'nav', 'main', 'aside',
  'table', 'form', 'fieldset', 'details', 'figure', 'ul', 'ol', 'dl'
]);

const BLOCK_TAGS_PATTERN = new RegExp(`<(${[...BLOCK_TAGS].join('|')})(\\s[^>]*)?>`, 'gi');

const STRUCTURAL_MARKERS = /<(head|body|\/html)[\s>]/gi;
const CONFIRMATION_WINDOW = 1000;

export function extractHtmlFragments(content) {
  const codeBlockRanges = getCodeBlockRanges(content);
  const fragments = [];
  const tagPattern = BLOCK_TAGS_PATTERN;

  let match;
  while ((match = tagPattern.exec(content)) !== null) {
    const tagName = match[1].toLowerCase();
    if (isInsideCodeBlock(match.index, codeBlockRanges)) continue;

    const openTagLen = match[0].length;

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

    if (htmlCode.length < 100) {
      const inner = htmlCode.slice(openTagLen, htmlCode.length - (closeMatchEnd - innerMatch.index));
      if (!/<(\w+)[\s>]/i.test(inner)) continue;
    }

    fragments.push({ start: match.index, end: closeMatchEnd, code: htmlCode });
  }

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

export function splitMixed(content) {
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

export function detectHtmlType(content) {
  const trimmed = content.trim();
  if (!trimmed) return 'none';
  if (/^<!DOCTYPE\s+html/i.test(trimmed) || /^<html[\s>]/i.test(trimmed)) {
    return 'full';
  }
  const fragments = extractHtmlFragments(content);
  return fragments.length > 0 ? 'mixed' : 'none';
}

export function findEmbeddedHtmlDoc(content, codeBlockRanges) {
  const re = /(^|\n)\s*(<!DOCTYPE\s+html|<html[\s>])/gim;
  let match;
  while ((match = re.exec(content)) !== null) {
    const docStart = match.index + match[1].length;
    if (isInsideCodeBlock(docStart, codeBlockRanges)) continue;

    const matchedByDoctype = /^<!DOCTYPE\s+html/i.test(match[2]);
    if (!matchedByDoctype) {
      const windowEnd = Math.min(docStart + CONFIRMATION_WINDOW, content.length);
      const ahead = content.slice(match.index, windowEnd);
      const structuralMatches = [...ahead.matchAll(STRUCTURAL_MARKERS)];
      if (structuralMatches.length < 1) continue;
    }

    const closeRe = /<\/html\s*>/gi;
    closeRe.lastIndex = docStart;
    const closeMatch = closeRe.exec(content);
    if (!closeMatch) continue;

    const docEnd = closeMatch.index + closeMatch[0].length;
    const after = content.slice(docEnd).trimStart();

    return {
      before: content.slice(0, docStart).trimEnd(),
      htmlDoc: content.slice(docStart, docEnd).trim(),
      after,
    };
  }
  return null;
}
