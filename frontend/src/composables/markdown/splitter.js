// ── 分段算法与代码块范围 ──────────────────────

export function splitParagraphs(content) {
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

export function getCodeBlockRanges(content) {
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

export function isInsideCodeBlock(pos, ranges) {
  return ranges.some(r => pos >= r.start && pos < r.end);
}
