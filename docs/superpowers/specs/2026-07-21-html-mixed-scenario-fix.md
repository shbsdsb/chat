# 混合场景 HTML 检测修复 — 设计规格

**日期**: 2026-07-21
**状态**: 设计完成，待实现
**关联**: 修复 1.1.3 引入的 `detectHtmlType` 仅检查开头的 Bug

---

## 1. 问题根因

`detectHtmlType(content)` 仅对 `trim()` 后的**开头**做完整 HTML 文档匹配：

```javascript
if (/^<!DOCTYPE\s+html/i.test(trimmed) || /^<html[\s>]/i.test(trimmed)) {
  return 'full';
}
```

当 AI 回复为"**文本/Markdown + 完整 HTML 文档**"时（如：介绍文字后接 `<!DOCTYPE html>...<html>...</html>`），开头是文本而非 `<!DOCTYPE`，`detectHtmlType` 返回 `"mixed"`。随后 `extractHtmlFragments` 只提取白名单标签（div/table 等），`<html>`、`<head>`、`<body>`、`<style>` 等结构标签落入 markdown-it → DOMPurify 管道，被剥离后产生**裸 CSS 文本泄露、标签残片**等混乱渲染。

**影响的混合场景：**

| 场景 | AI 输出格式 | 当前行为 | 期望 |
|------|-----------|---------|------|
| `md + html` | Markdown 介绍 + `<!DOCTYPE html>...` | 混乱（结构标签被 DOMPurify 剥离） | 文本 md 渲染 + HTML iframe 渲染 |
| `txt + html` | 纯文本介绍 + `<!DOCTYPE html>...` | 混乱 | 文本显示 + HTML iframe 渲染 |
| `txt + md + html` | 文本 + Markdown + HTML 文档 | 混乱 | 文本+md 渲染 + HTML iframe 渲染 |
| `html + txt` | `<!DOCTYPE html>...` + 尾部说明文本 | 正常（走 full 路径） ✓ | 保持不变 |
| `md + 片段` | Markdown + `<div>...</div>` | 正常（走 mixed 路径） ✓ | 保持不变 |
| `纯 html` | `<!DOCTYPE html>...` | 正常（走 full 路径） ✓ | 保持不变 |

---

## 2. 解决方案

### 2.1 架构调整

将 `detectHtmlType` + `splitMixed` 两阶段替换为统一的 `analyzeContent(content)`：

```
analyzeContent(content)                      ← 新函数
    │
    ├── ① 开头即完整 HTML 文档 → "full"
    │       → blocks = [{ type:'html', code:content }]
    │
    ├── ② 内容中间嵌入完整 HTML 文档 → "embedded_html"
    │       → blocks = [before(text), { type:'html', code:htmlDoc }, after(text)]
    │
    ├── ③ 无完整文档，有 BLOCK_TAGS 片段 → "mixed"
    │       → blocks = splitMixed(...)   (现有逻辑不变)
    │
    └── ④ 纯文本/Markdown → "none"
            → 现有 frozenHtmls / liveHtml 流程
```

### 2.2 完整 HTML 文档判定规则

**判定为完整 HTML 文档的条件**（满足任一）：

1. 以 `<!DOCTYPE html>` 开头（忽略大小写、前导空白）— 现有规则
2. 以 `<html` 标签开头（忽略大小写）— 现有规则
3. **新增**：在非代码块区域内出现独立的 `<!DOCTYPE html>` 或行首 `<html` 标记

**防假阳性策略**（分级）：

| 匹配到 | 假阳性风险 | 处理 |
|--------|----------|------|
| `<!DOCTYPE html>` | 零（自然语言中几乎不可能出现） | **无需确认**，直接提取 |
| `<html` | 有（如"请参考 `<html>` 标签"） | 需 ≥1 个结构标记（`<head`/`<body`/`</html`）在后续 1000 字符内 |

这保证极简文档（如 `<!DOCTYPE html><html><title>Test</title></html>`）也能被正确识别（`<!DOCTYPE` 匹配→免确认），同时 `<html` 匹配不会被"请参考 `<html>` 标签"这类文本触发。

```javascript
// 嵌入式 HTML 文档匹配正则
const EMBEDDED_HTML_RE = /(^|\n)\s*(<!DOCTYPE\s+html|<html[\s>])/gim;

// 结构确认：仅 <html> 匹配时需要，<!DOCTYPE> 匹配跳过
const STRUCTURAL_MARKERS = /<(head|body|\/html)[\s>]/gi;
const CONFIRMATION_WINDOW = 1000;
```

### 2.3 HTML 文档范围提取

找到起始标记后，定位文档结束位置：

1. 优先查找 `</html>` 闭合标签（忽略大小写）
2. 如找不到，以内容末尾为结束位置
3. 提取的 HTML 代码作为 **html block**，前后内容作为 **text block**

```javascript
function findEmbeddedHtmlDoc(content, codeBlockRanges) {
  const re = /(^|\n)\s*(<!DOCTYPE\s+html|<html[\s>])/gim;
  let match;
  while ((match = re.exec(content)) !== null) {
    const docStart = match.index + match[1].length; // 跳过前导换行
    if (isInsideCodeBlock(docStart, codeBlockRanges)) continue;

    // 结构确认（分级）：
    // - <!DOCTYPE html> → 强信号，免确认
    // - <html> → 需 ≥1 个结构标记在后续 1000 字符内
    const matchedByDoctype = /^<!DOCTYPE\s+html/i.test(match[2]);
    if (!matchedByDoctype) {
      const windowEnd = Math.min(docStart + CONFIRMATION_WINDOW, content.length);
      const ahead = content.slice(match.index, windowEnd);
      const structuralMatches = [...ahead.matchAll(STRUCTURAL_MARKERS)];
      if (structuralMatches.length < 1) continue; // 结构确认失败，跳过
    }

    // 找闭合 </html> — 使用第一个（文档内部出现字面量的概率极低）
    const closeRe = /<\/html\s*>/gi;
    closeRe.lastIndex = docStart;
    const closeMatch = closeRe.exec(content);
    // 必须找到 </html> 闭合标签才提取（流式中未闭合文档不提取）
    if (!closeMatch) continue;
    const docEnd = closeMatch.index + closeMatch[0].length;

    // after 部分递归走 splitMixed 捕获残留 HTML 片段
    const after = content.slice(docEnd).trimStart();

    return {
      before: content.slice(0, docStart).trimEnd(),
      htmlDoc: content.slice(docStart, docEnd).trim(),
      after,
    };
  }
  return null;
}
```

### 2.4 自然覆盖所有组合

| # | 场景 | before | htmlDoc | after | 路径 |
|---|------|--------|---------|-------|------|
| 1 | 纯 HTML | — | ✔ | — | ① full |
| 2 | txt + html | `介绍文字` | `<!DOCTYPE>...` | — | ② embedded |
| 3 | md + html | `**粗体**介绍` | `<!DOCTYPE>...` | — | ② embedded |
| 4 | txt + md + html | `文本\n\n**粗体**` | `<!DOCTYPE>...` | — | ② embedded |
| 5 | html + txt | — | `<!DOCTYPE>...` | `补充说明` | ② embedded |
| 6 | txt + html + txt | `前言` | `<!DOCTYPE>...` | `后记` | ② embedded |
| 7 | md + 片段 | `介绍\n\n<div>...</div>` | — | — | ③ mixed |
| 8 | 纯文本/md | `普通文本` | — | — | ④ none |

---

## 3. 代码改动范围

**仅修改 1 个文件：**

| 文件 | 改动 |
|------|------|
| `frontend/src/composables/useMarkdown.js` | 新增 `findEmbeddedHtmlDoc`（~30行）；重构 composable watch 的四路径调度（~20行调整） |

**不改动：** `MessageBubble.vue`、`HtmlPreview.vue`、后端、store、router。

`MessageBubble` 无需修改的原因：`embedded_html` 路径产出的 `blocks` 格式与现有 `mixed` 路径完全一致（`[{type:'text',html}, {type:'html',code}, ...]`），现有渲染逻辑直接复用。

---

## 4. useMarkdown composable 新调度逻辑

```javascript
watch(content) → {
  if (!content) {
    frozenHtmls = []; liveHtml = '';
    blocks = []; isCompleteHtml = false;
    return
  }

  // ① full — 开头即完整 HTML（现有逻辑）
  if (detectHtmlType(content) === 'full') {
    frozenHtmls = []; liveHtml = '';
    blocks = [{ type:'html', code:content }]
    isCompleteHtml = true
    return
  }
  isCompleteHtml = false

  // ② embedded_html — 新增：内容中间嵌入完整 HTML 文档
  const embedded = findEmbeddedHtmlDoc(content, getCodeBlockRanges(content))
  if (embedded) {
    frozenHtmls = []; liveHtml = '';          // ★ 显式清除旧状态
    blocks = []; isCompleteHtml = false;

    const rendered = []

    // before 文本 → markdown 渲染
    if (embedded.before) {
      rendered.push({ type:'text', html:safeRender(embedded.before) })
    }

    // HTML 文档 → iframe 渲染
    rendered.push({ type:'html', code:embedded.htmlDoc })

    // after 部分：先递归走 splitMixed 捕获残留 HTML 片段
    // 防止 "后记 + <div>片段</div>" 中的片段被当纯文本漏掉
    const afterBlocks = splitMixed(embedded.after)
    for (const b of afterBlocks) {
      if (b.type === 'text') {
        if (b.content.trim()) rendered.push({ type:'text', html:safeRender(b.content) })
      } else {
        rendered.push(b)
      }
    }

    blocks = rendered
    return
  }

  // ③ mixed — 现有逻辑（BLOCK_TAGS 片段）
  if (detectHtmlType(content) === 'mixed') { ... }

  // ④ none — 现有逻辑（纯文本/Markdown）
  ...
}
```

---

## 5. 边缘情况

| 场景 | 处理 |
|------|------|
| `<!DOCTYPE html>` 在代码块内 | `isInsideCodeBlock` 跳过，不触发 |
| 文本中出现 `<html>` 字面引用 | 分级确认：`<!DOCTYPE html>` 匹配免检；`<html>` 匹配需 ≥1 个 `<head>/<body>/</html>` 标记在后续 1000 字符内 |
| HTML 文档内部含 `</html>` 字面量 | 使用**第一个** `</html>` 闭合（文档内部出现概率极低，尾部出现更常见） |
| HTML 文档无 `</html>` 闭合（流式中常见） | `findEmbeddedHtmlDoc` 返回 `null`，走 `none` 路径（markdown 渲染）；待闭合后下一次 watch 触发自动切换 |
| after 部分含 HTML 片段（`<div>...</div>`） | `splitMixed(after)` 递归提取，不丢失 |
| after 部分为空 | `splitMixed` 返回空数组，无多余 text block |
| HTML 文档含中文/Emoji | `before`/`after` 走 markdown-it，UTF-8 安全 |
| 多个 `<!DOCTYPE>` 出现 | 只提取第一个（循环中提前 return） |
| 流式渲染中 | 仅冻结段走 `findEmbeddedHtmlDoc`；末尾未闭合段保持 markdown 渲染 |
| 编辑模式 | 始终显示 textarea，不做 HTML 检测 |
| 流式期间状态残留 | ★ 所有路径显式重置 `frozenHtmls/liveHtml/blocks/isCompleteHtml` 四个 ref |

---

## 6. 非目标

- 不修改 `BLOCK_TAGS` 白名单（`html`/`head`/`body`/`style` 作为完整文档整体提取，无需加入）
- 不修改 `HtmlPreview` 组件
- 不修改 `MessageBubble` 模板
- 不修改后端 API
- 不添加多 HTML 文档提取（第一条之后的忽略）
