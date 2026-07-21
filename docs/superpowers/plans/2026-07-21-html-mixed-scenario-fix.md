# 混合场景 HTML 检测修复 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 `detectHtmlType` 仅检查开头的 Bug，支持"文本+HTML 文档"等 8 种混合场景自动检测

**Architecture:** 在 useMarkdown composable 中新增 `findEmbeddedHtmlDoc` 扫描内容中间的 `<!DOCTYPE html>` / `<html` 标记（分级结构确认），composable watch 新增 `embedded_html` 路径介于 `full` 和 `mixed` 之间，after 递归走 `splitMixed`

**Tech Stack:** Vue 3 Composition API, JavaScript

## Global Constraints

- 仅修改 `frontend/src/composables/useMarkdown.js`（不改 MessageBubble / HtmlPreview / 后端 / store / router）
- `<!DOCTYPE html>` 匹配免结构确认，`<html>` 匹配需 ≥1 个 `<head>/<body>/</html>` 标记在后续 1000 字符内
- 使用**第一个** `</html>` 作为文档闭合点
- after 部分必须递归走 `splitMixed` 捕获残留 HTML 片段
- 所有路径显式重置 `frozenHtmls`/`liveHtml`/`blocks`/`isCompleteHtml` 四个 ref
- 构建通过：`cd frontend && npm run build`

---

### Task 1: 添加 findEmbeddedHtmlDoc 函数

**Files:**
- Modify: `frontend/src/composables/useMarkdown.js`（在 `detectHtmlType` 函数之后、composable 之前插入）

**Interfaces:**
- Produces: `findEmbeddedHtmlDoc(content, codeBlockRanges)` → `{ before, htmlDoc, after } | null`
- Produces: `STRUCTURAL_MARKERS`, `CONFIRMATION_WINDOW` (module-level 常量)

- [ ] **Step 1: 在 `detectHtmlType` 函数之后插入常量和新函数**

在 `detectHtmlType` 的闭合 `}` 之后、`// ── composable ──` 注释之前插入：

```javascript
// ── 嵌入式 HTML 文档检测 ──────────────────────

const STRUCTURAL_MARKERS = /<(head|body|\/html)[\s>]/gi;
const CONFIRMATION_WINDOW = 1000;

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

    // 找闭合 </html> — 使用第一个；未闭合则跳过（流式安全）
    const closeRe = /<\/html\s*>/gi;
    closeRe.lastIndex = docStart;
    const closeMatch = closeRe.exec(content);
    if (!closeMatch) continue; // 未闭合 → 不提取，走 none 路径
    const docEnd = closeMatch.index + closeMatch[0].length;

    // after 部分供 composable 递归走 splitMixed
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

- [ ] **Step 2: 验证构建**

```bash
cd frontend && npm run build 2>&1 | tail -3
```

预期: `✓ built in ...` 无报错（函数尚未被调用，无引用错误）

- [ ] **Step 3: 提交**

```bash
git add frontend/src/composables/useMarkdown.js
git commit -m "feat: add findEmbeddedHtmlDoc with tiered structural confirmation"
```

---

### Task 2: 集成 embedded_html 路径到 composable watch

**Files:**
- Modify: `frontend/src/composables/useMarkdown.js`（composable 的 watch 回调）

**Interfaces:**
- Consumes: `findEmbeddedHtmlDoc(content, codeBlockRanges)` (Task 1)
- Consumes: `splitMixed(content)` (existing), `safeRender(text)` (existing)
- Modifies: composable `watch` callback — 在 `full` 和 `mixed` 路径之间插入 `embedded_html` 路径

- [ ] **Step 1: 在 composable watch 中插入 embedded_html 路径**

定位到 `watch` 回调中 `// ── 完整 HTML 文档 ──` 块的 `return` 之后、`// ── 混合内容 ──` 之前，插入以下代码：

注意：需要先读取当前文件确认精确位置。插入位置在 `isCompleteHtml.value = false;` 之后。

替换从 `isCompleteHtml.value = false;` 到 `// ── 混合内容 ──` 之间的内容为：

```javascript
      isCompleteHtml.value = false;

      // ── 嵌入式 HTML 文档 ──
      const embedded = findEmbeddedHtmlDoc(content, getCodeBlockRanges(content));
      if (embedded) {
        frozenHtmls.value = [];
        liveHtml.value = '';
        blocks.value = [];
        isCompleteHtml.value = false;

        const rendered = [];

        // before 文本 → markdown 渲染
        if (embedded.before) {
          rendered.push({ type: 'text', html: safeRender(embedded.before) });
        }

        // HTML 文档 → iframe 渲染
        try {
          rendered.push({ type: 'html', code: embedded.htmlDoc });
        } catch {
          // HTML 文档本身有问题，降级为 markdown
          rendered.push({ type: 'text', html: safeRender(embedded.htmlDoc) });
        }

        // after 部分递归走 splitMixed 捕获残留 HTML 片段
        try {
          const afterBlocks = splitMixed(embedded.after);
          for (const b of afterBlocks) {
            if (b.type === 'text') {
              if (b.content.trim()) rendered.push({ type: 'text', html: safeRender(b.content) });
            } else {
              rendered.push(b);
            }
          }
        } catch {
          if (embedded.after.trim()) {
            rendered.push({ type: 'text', html: safeRender(embedded.after) });
          }
        }

        blocks.value = rendered;
        return;
      }

      // ── 混合内容 ──
```

- [ ] **Step 2: 验证构建**

```bash
cd frontend && npm run build 2>&1 | tail -3
```

预期: `✓ built in ...`

- [ ] **Step 3: 提交**

```bash
git add frontend/src/composables/useMarkdown.js
git commit -m "feat: integrate embedded HTML doc detection into composable watch"
```

---

### Task 3: 端到端验证

**Files:**
- 无代码改动

- [ ] **Step 1: 验证构建 + 后端测试**

```bash
cd frontend && npm run build 2>&1 | tail -3
cd ../backend && python -m pytest -q 2>&1
```

预期: `✓ built in ...` + `39 passed`

- [ ] **Step 2: 手动验证 8 个场景**

启动 `cd frontend && npm run dev`，逐一测试：

| # | 场景 | 测试输入 | 预期 |
|---|------|---------|------|
| 1 | 纯 HTML | `<!DOCTYPE html><html><body>Hello</body></html>` | iframe 渲染 |
| 2 | txt + html | `介绍文字\n\n<!DOCTYPE html><html><body>Hi</body></html>` | 文本 + iframe |
| 3 | md + html | `**粗体**\n\n<!DOCTYPE html><html><body>Hi</body></html>` | md渲染 + iframe |
| 4 | txt + md + html | `文本\n\n**粗体**\n\n<!DOCTYPE html><html>...</html>` | 文本+md + iframe |
| 5 | html + txt | `<!DOCTYPE html><html>...</html>\n\n补充说明` | iframe + 文本 |
| 6 | txt + html + txt | `前言\n\n<!DOCTYPE html>...</html>\n\n后记` | 文本 + iframe + 文本 |
| 7 | md + 片段 | `**粗体**\n\n<div class="x">hi</div>` | md + iframe片段 |
| 8 | 纯文本 | `普通文本` | markdown渲染 |
| 9 | 假阳性 | `请参考 <html> 标签的用法` | 纯文本（不触发） |
| 10 | 极简文档 | `<!DOCTYPE html><html><title>T</title></html>` | iframe渲染 |
| 11 | 流式未闭合 | AI 流式输出中 `<!DOCTYPE html><html>...` 尚未出现 `</html>` | markdown渲染，不提取 |

- [ ] **Step 3: 提交（如有遗留文件）**

```bash
git status
```
