# 代码库重构 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 消除死代码和重复模式，拆分臃肿文件，在不改变 API 契约的前提下提升可维护性。

**Architecture:** 分 3 个 PR（P0→P1→P2），每个阶段独立可测。P0 删除死代码并提取 BaseDialog；P1 拆分 useMarkdown、提取共享常量和 Drawer 复用逻辑；P2 拆分 storage、提取 stream_handler/http_client、精简路由样板和 chat.js store。

**Tech Stack:** Vue 3 / Pinia / Vite (前端), Flask / Python (后端), pytest (测试)

## Global Constraints

- API 响应格式 `{code, message, data}` 不变
- 所有路由端点 URL、方法、参数签名不变
- `user_data/` 下 JSON 文件格式不变
- Vue 组件 props/emits/slots 签名不变
- `cd backend && python -m pytest` 39 tests 全部通过
- 重构前后数据完全互通

---

# 阶段一：P0（PR #1）— 死代码 + BaseDialog

## 文件结构

```
删除:
  backend/app/database.py
  user_data/chat.db
  backend/tests/user_data/chat.db

新增:
  frontend/src/components/BaseDialog.vue

修改:
  frontend/src/components/ConversationItem.vue
  frontend/src/components/PresetSelector.vue
  frontend/src/components/AlertDialog.vue
```

---

### Task P0-1: 删除 SQLite 死代码与遗留文件

**Files:**
- Delete: `backend/app/database.py`
- Delete: `user_data/chat.db`
- Delete: `backend/tests/user_data/chat.db`

**Interfaces:**
- Consumes: 无
- Produces: 无（纯删除）

- [ ] **Step 1: 确认零引用**

```bash
cd backend && grep -rn "from.*database\|import.*database" app/ tests/
```

Expected: 无输出（确认无任何 import）

- [ ] **Step 2: 删除文件**

```bash
rm backend/app/database.py
rm user_data/chat.db
rm backend/tests/user_data/chat.db
```

- [ ] **Step 3: 运行全部测试确认无破坏**

```bash
cd backend && python -m pytest -v
```

Expected: 39 passed, 0 failed

- [ ] **Step 4: Commit**

```bash
git add backend/app/database.py user_data/chat.db backend/tests/user_data/chat.db
git commit -m "chore: remove deprecated SQLite database module and leftover .db files"
```

---

### Task P0-2: 创建 BaseDialog.vue 通用弹窗组件

**Files:**
- Create: `frontend/src/components/BaseDialog.vue`

**Interfaces:**
- Produces:
  - `BaseDialog` 组件
  - Props: `visible: Boolean`, `title: String`
  - Emits: `close`
  - Slots: `default`（内容区）, `footer`（底部按钮区，可选）

- [ ] **Step 1: 创建 BaseDialog.vue**

```vue
<template>
  <Teleport to="body">
    <div v-if="visible" class="dialog-overlay" @click.self="$emit('close')">
      <div class="dialog-box">
        <div class="dialog-title">{{ title }}</div>
        <div class="dialog-body">
          <slot />
        </div>
        <div v-if="$slots.footer" class="dialog-actions">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  title: { type: String, default: '' },
});

defineEmits(['close']);
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-box {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  width: 360px;
  max-width: 90vw;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.18);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dialog-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.dialog-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 全局样式（非 scoped，供子组件复用） */
:deep(.dialog-input) {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d5d5d5;
  border-radius: 8px;
  font-size: 14px;
  color: #333;
  outline: none;
  font-family: inherit;
  box-sizing: border-box;
}
:deep(.dialog-input:focus) {
  border-color: #4a90d9;
  box-shadow: 0 0 0 2px rgba(74, 144, 217, 0.15);
}

:deep(.dialog-btn) {
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid transparent;
  transition: background 0.15s, color 0.15s;
  font-family: inherit;
}

:deep(.dialog-btn-cancel) {
  background: #f5f5f5;
  color: #666;
  border-color: #ddd;
}
:deep(.dialog-btn-cancel:hover) {
  background: #e8e8e8;
  color: #333;
}

:deep(.dialog-btn-ok) {
  background: #4a90d9;
  color: #fff;
}
:deep(.dialog-btn-ok:hover:not(:disabled)) {
  background: #357abd;
}
:deep(.dialog-btn-ok:disabled) {
  opacity: 0.4;
  cursor: default;
}

:deep(.dialog-btn-danger) {
  background: #ef5350;
  color: #fff;
}
:deep(.dialog-btn-danger:hover) {
  background: #d32f2f;
}

/* 危险对话框额外样式 */
:deep(.dialog-danger) {
  width: 360px;
  text-align: center;
  border-top: 3px solid #ef5350;
}

:deep(.dialog-danger-icon) {
  display: flex;
  justify-content: center;
}

:deep(.dialog-danger-msg) {
  font-size: 14px;
  color: #555;
  line-height: 1.6;
  margin: 0;
}
</style>
```

- [ ] **Step 2: Commit BaseDialog**

```bash
git add frontend/src/components/BaseDialog.vue
git commit -m "feat: add BaseDialog reusable dialog component"
```

---

### Task P0-3: 改造 ConversationItem.vue 使用 BaseDialog

**Files:**
- Modify: `frontend/src/components/ConversationItem.vue`

**Interfaces:**
- Consumes: `BaseDialog`（Props: visible, title; Emits: close; Slots: default, footer）
- 组件对外 props/emits 不变

- [ ] **Step 1: 替换重命名弹窗模板**

将 L18-36 的 `<Teleport>` 块替换为 `BaseDialog`：

旧代码（L18-36）：
```vue
    <!-- 重命名弹窗 -->
    <Teleport to="body">
      <div v-if="showRename" class="dialog-overlay" @click.self="cancelRename">
        <div class="dialog-box">
          <div class="dialog-title">重命名</div>
          <input
            ref="nameInput"
            v-model="newName"
            class="dialog-input"
            placeholder="输入新名称"
            @keydown.enter="confirmRename"
            @keydown.escape="cancelRename"
          />
          <div class="dialog-actions">
            <button class="dialog-btn dialog-btn-cancel" @click="cancelRename">取消</button>
            <button class="dialog-btn dialog-btn-ok" @click="confirmRename" :disabled="!newName.trim()">确定</button>
          </div>
        </div>
      </div>
    </Teleport>
```

新代码：
```vue
    <!-- 重命名弹窗 -->
    <BaseDialog :visible="showRename" title="重命名" @close="cancelRename">
      <input
        ref="nameInput"
        v-model="newName"
        class="dialog-input"
        placeholder="输入新名称"
        @keydown.enter="confirmRename"
        @keydown.escape="cancelRename"
      />
      <template #footer>
        <button class="dialog-btn dialog-btn-cancel" @click="cancelRename">取消</button>
        <button class="dialog-btn dialog-btn-ok" @click="confirmRename" :disabled="!newName.trim()">确定</button>
      </template>
    </BaseDialog>
```

- [ ] **Step 2: 替换删除确认弹窗模板**

将 L39-52 的 `<Teleport>` 块替换为 `BaseDialog`：

旧代码（L39-52）：
```vue
    <!-- 删除确认弹窗 -->
    <Teleport to="body">
      <div v-if="showDelete" class="dialog-overlay" @click.self="cancelDelete">
        <div class="dialog-box dialog-danger">
          <div class="dialog-danger-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#ef5350" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          </div>
          <p class="dialog-danger-msg">确定要删除对话「{{ conversation.title }}」吗？此操作不可撤销。</p>
          <div class="dialog-actions">
            <button class="dialog-btn dialog-btn-cancel" @click="cancelDelete">取消</button>
            <button class="dialog-btn dialog-btn-danger" @click="confirmDelete">确定删除</button>
          </div>
        </div>
      </div>
    </Teleport>
```

新代码：
```vue
    <!-- 删除确认弹窗 -->
    <BaseDialog :visible="showDelete" title=" " @close="cancelDelete">
      <div class="dialog-danger">
        <div class="dialog-danger-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#ef5350" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        </div>
        <p class="dialog-danger-msg">确定要删除对话「{{ conversation.title }}」吗？此操作不可撤销。</p>
      </div>
      <template #footer>
        <button class="dialog-btn dialog-btn-cancel" @click="cancelDelete">取消</button>
        <button class="dialog-btn dialog-btn-danger" @click="confirmDelete">确定删除</button>
      </template>
    </BaseDialog>
```

- [ ] **Step 3: 添加 BaseDialog import**

在 `<script setup>` 中添加（L56 附近）：

```js
import BaseDialog from "@/components/BaseDialog.vue";
```

- [ ] **Step 4: 删除重复的 dialog CSS**

删除 L171-279 所有 `.dialog-*` 样式（这些现在由 BaseDialog 全局提供）。

删除范围：
```
/* ── 弹窗 ─────────────────────────────────────── */
.dialog-overlay { ... }
.dialog-box { ... }
.dialog-title { ... }
.dialog-input { ... }
.dialog-actions { ... }
.dialog-btn { ... }
.dialog-btn-cancel { ... }
.dialog-btn-ok { ... }
.dialog-btn-danger { ... }
.dialog-danger { ... }
.dialog-danger-icon { ... }
.dialog-danger-msg { ... }
```

- [ ] **Step 5: 验证**

```bash
cd frontend && npm run build  # 确认无编译错误
```

手动验证：创建/重命名/删除会话弹窗样式与交互行为与改造前一致。

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ConversationItem.vue
git commit -m "refactor: replace inline dialogs with BaseDialog in ConversationItem"
```

---

### Task P0-4: 改造 AlertDialog.vue 使用 BaseDialog

**Files:**
- Modify: `frontend/src/components/AlertDialog.vue`

**Interfaces:**
- Consumes: `BaseDialog`
- 组件对外 props/emits 不变

- [ ] **Step 1: 替换模板**

将模板替换为使用 `BaseDialog`。保留现有 `AlertDialog.vue` 中特有的 `confirmText`/`cancelText` props 和 emit 逻辑，仅替换 overlay/box 结构。

```vue
<template>
  <BaseDialog
    :visible="visible"
    :title="title"
    @close="handleCancel"
  >
    <p class="alert-message">{{ message }}</p>
    <template #footer>
      <button
        v-if="showCancel"
        class="dialog-btn dialog-btn-cancel"
        @click="handleCancel"
      >{{ cancelText }}</button>
      <button
        class="dialog-btn dialog-btn-ok"
        @click="handleConfirm"
      >{{ confirmText }}</button>
    </template>
  </BaseDialog>
</template>
```

- [ ] **Step 2: 添加 import 并删除重复 CSS**

```js
import BaseDialog from "@/components/BaseDialog.vue";
```

删除 `<style scoped>` 中 `.dialog-overlay`、`.dialog-box`、`.dialog-title`、`.dialog-actions` 样式（这些已在 BaseDialog 中），仅保留 `.alert-message` 等 Alert 特有样式。

- [ ] **Step 3: 验证**

```bash
cd frontend && npm run build
```

手动验证：全局 Alert/确认弹窗样式一致。

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/AlertDialog.vue
git commit -m "refactor: AlertDialog uses BaseDialog"
```

---

### Task P0-5: 改造 PresetSelector.vue 使用 BaseDialog

**Files:**
- Modify: `frontend/src/components/PresetSelector.vue`

**Interfaces:**
- Consumes: `BaseDialog`
- 组件对外 props/emits 不变

- [ ] **Step 1: 替换弹窗模板**

PresetSelector 有多个弹窗（删除确认、命名等），逐个替换。每个 `<Teleport><div class="dialog-overlay">...</div></Teleport>` 替换为 `<BaseDialog>`。

- [ ] **Step 2: 添加 import**

```js
import BaseDialog from "@/components/BaseDialog.vue";
```

- [ ] **Step 3: 删除重复 CSS**

删除 `.dialog-overlay`、`.dialog-box`、`.dialog-title`、`.dialog-input`、`.dialog-actions`、`.dialog-btn-*` 等已在 BaseDialog 中定义的样式。

- [ ] **Step 4: 验证**

```bash
cd frontend && npm run build
```

手动验证：预设保存/删除/命名弹窗样式一致。

- [ ] **Step 5: P0 最终验证**

```bash
cd backend && python -m pytest -v   # 39 passed
cd frontend && npm run build        # 无错误
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/PresetSelector.vue
git commit -m "refactor: PresetSelector uses BaseDialog"

# 然后创建 PR #1
```

---

# 阶段二：P1（PR #2）— useMarkdown + 常量 + Drawer

三个子任务完全独立。

## 文件结构

```
新增:
  frontend/src/composables/markdown/engine.js
  frontend/src/composables/markdown/htmlDetector.js
  frontend/src/composables/markdown/splitter.js
  frontend/src/api/constants.js
  frontend/src/composables/useResizableDrawer.js
  frontend/src/assets/drawer.css

修改:
  frontend/src/composables/useMarkdown.js
  frontend/src/api/request.js
  frontend/src/api/sse.js
  frontend/src/components/ConversationsDrawer.vue
  frontend/src/components/SettingsDrawer.vue
```

---

### Task P1-1: 拆分 useMarkdown — engine.js

**Files:**
- Create: `frontend/src/composables/markdown/engine.js`

**Interfaces:**
- Produces:
  - `md: MarkdownIt` — 配置好的 markdown-it 实例（highlight.js 集成、HTML 允许）
  - `sanitize(html: string): string` — DOMPurify 清洗后的安全 HTML

- [ ] **Step 1: 创建 engine.js**

从 `useMarkdown.js` 中提取 markdown-it 初始化、highlight.js 配置、DOMPurify 实例化代码。

```js
// composables/markdown/engine.js
import MarkdownIt from "markdown-it";
import hljs from "highlight.js";
import DOMPurify from "dompurify";

const md = new MarkdownIt({
  html: true,
  breaks: true,
  linkify: true,
  typographer: true,
  highlight: (code, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre><code class="hljs language-${lang}">${hljs.highlight(code, { language: lang }).value}</code></pre>`;
      } catch {}
    }
    return `<pre><code class="hljs">${md.utils.escapeHtml(code)}</code></pre>`;
  },
});

// HTML 内联渲染：注册 fence renderer 注入复制按钮
const defaultFence = md.renderer.rules.fence;
md.renderer.rules.fence = (tokens, idx, options, env, self) => {
  const token = tokens[idx];
  const lang = token.info?.trim() || "";
  const code = token.content;
  const escaped = md.utils.escapeHtml(code);

  let highlighted;
  if (lang && hljs.getLanguage(lang)) {
    try {
      highlighted = hljs.highlight(code, { language: lang }).value;
    } catch {
      highlighted = escaped;
    }
  } else {
    highlighted = escaped;
  }

  const langLabel = lang ? `<span class="code-lang">${lang}</span>` : "";
  const copyBtn = `<button class="copy-btn" data-code="${md.utils.escapeHtml(code)}" title="复制代码">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
    </svg>
  </button>`;

  return `<div class="code-block-wrapper">
    <div class="code-block-header">${langLabel}${copyBtn}</div>
    <pre><code class="hljs${lang ? ` language-${lang}` : ""}">${highlighted}</code></pre>
  </div>`;
};

function sanitize(html) {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      "p", "br", "strong", "em", "u", "s", "del", "ins", "code", "pre",
      "h1", "h2", "h3", "h4", "h5", "h6",
      "ul", "ol", "li", "blockquote", "a", "img",
      "table", "thead", "tbody", "tr", "th", "td",
      "hr", "span", "div", "button", "svg", "path", "rect", "circle", "line",
      "polyline", "polygon", "html", "head", "body", "title", "meta", "link", "style", "script",
    ],
    ALLOWED_ATTR: [
      "href", "src", "alt", "title", "class", "id", "target", "rel",
      "data-code", "viewBox", "fill", "stroke", "stroke-width", "d",
      "width", "height", "xmlns", "rx", "ry", "x", "y",
    ],
  });
}

export { md, sanitize };
```

> 注意：复制上面的 md 初始化代码时，必须与当前 `useMarkdown.js` 中实际初始化代码保持一致（上述代码基于常见配置，需以源文件为准微调）。

- [ ] **Step 2: Commit**

```bash
git add frontend/src/composables/markdown/engine.js
git commit -m "refactor: extract markdown engine (md/hljs/DOMPurify) from useMarkdown"
```

---

### Task P1-2: 拆分 useMarkdown — htmlDetector.js

**Files:**
- Create: `frontend/src/composables/markdown/htmlDetector.js`

**Interfaces:**
- Produces:
  - `detectHtmlType(code: string): string` — 返回 'complete' | 'body' | 'none'
  - `findEmbeddedHtmlDoc(html: string): object|null` — 返回 { type, code, start, end } 或 null
  - `extractHtmlFragments(html: string): array` — 返回 HTML 片段数组

- [ ] **Step 1: 创建 htmlDetector.js**

从 `useMarkdown.js` 中复制 `detectHtmlType`、`findEmbeddedHtmlDoc`、`extractHtmlFragments` 三个函数到新文件（保持实现完全不变）。

```js
// composables/markdown/htmlDetector.js

export function detectHtmlType(code) {
  // 从 useMarkdown.js 完整复制
}

export function findEmbeddedHtmlDoc(html) {
  // 从 useMarkdown.js 完整复制
}

export function extractHtmlFragments(html) {
  // 从 useMarkdown.js 完整复制
}
```

> 注意：以 `useMarkdown.js` 中的实际实现为准，此处省略细节以避免不一致。

- [ ] **Step 2: Commit**

```bash
git add frontend/src/composables/markdown/htmlDetector.js
git commit -m "refactor: extract HTML detector functions from useMarkdown"
```

---

### Task P1-3: 拆分 useMarkdown — splitter.js

**Files:**
- Create: `frontend/src/composables/markdown/splitter.js`

**Interfaces:**
- Produces:
  - `splitParagraphs(text: string): string[]` — 按 `\n\n` 分段
  - `splitMixed(text: string): array` — 混合分段（Markdown + HTML 片段）
  - `computeCodeBlockRanges(text: string): array` — 代码块范围计算

- [ ] **Step 1: 创建 splitter.js**

从 `useMarkdown.js` 中完整复制分段相关函数。

```js
// composables/markdown/splitter.js

export function splitParagraphs(text) {
  // 从 useMarkdown.js 完整复制
}

export function splitMixed(text) {
  // 从 useMarkdown.js 完整复制
}

export function computeCodeBlockRanges(text) {
  // 从 useMarkdown.js 完整复制
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/composables/markdown/splitter.js
git commit -m "refactor: extract paragraph splitter from useMarkdown"
```

---

### Task P1-4: 精简 useMarkdown.js 为组合入口

**Files:**
- Modify: `frontend/src/composables/useMarkdown.js`

**Interfaces:**
- 对外 export 的 `useMarkdown()` 返回值完全不变

- [ ] **Step 1: 替换 import + 删除已提取的函数**

```js
// composables/useMarkdown.js（精简后）
import { ref, watch } from "vue";
import { md, sanitize } from "./markdown/engine";
import { extractHtmlFragments } from "./markdown/htmlDetector";
import { splitMixed } from "./markdown/splitter";

export function useMarkdown(textSource) {
  // 仅保留 composable 逻辑：ref、watch、分段冻结策略
  // 使用 import 来的 md.render()、sanitize()、splitMixed()、extractHtmlFragments()
  // ...（完整 composable 逻辑不变）
}
```

注意：原文件中 `detectHtmlType`、`findEmbeddedHtmlDoc`、`splitParagraphs`、`computeCodeBlockRanges` 的函数定义需删除（已移到子模块），仅保留 composable 函数体和 watch。

- [ ] **Step 2: 验证编译**

```bash
cd frontend && npm run build
```

确认无 import 错误。

- [ ] **Step 3: 手动验证 Markdown 渲染**

打开应用，发送包含代码块、列表、HTML 片段的 Markdown 内容，确认渲染与重构前一致。

- [ ] **Step 4: Commit**

```bash
git add frontend/src/composables/useMarkdown.js
git commit -m "refactor: slim useMarkdown to composition entry point"
```

---

### Task P1-5: 提取 HTTP_STATUS_MSG 到 api/constants.js

**Files:**
- Create: `frontend/src/api/constants.js`
- Modify: `frontend/src/api/request.js`
- Modify: `frontend/src/api/sse.js`

**Interfaces:**
- Produces:
  - `HTTP_STATUS_MSG: { [code: number]: string }`
  - `getAlert(): AlertStore | null`

- [ ] **Step 1: 创建 api/constants.js**

```js
// api/constants.js
import { useAlertStore } from "@/stores/alert";

export const HTTP_STATUS_MSG = {
  400: "请求参数有误，请检查输入内容",
  401: "认证失败，请检查 API Key 是否正确",
  402: "账户余额不足，请充值后重试",
  403: "没有访问权限，请检查 API Key 权限",
  404: "请求的资源不存在",
  405: "请求方法不被允许",
  408: "请求超时，请检查网络后重试",
  409: "资源冲突，请刷新后重试",
  410: "请求的资源已被永久删除",
  413: "请求体过大",
  415: "不支持的媒体类型",
  422: "请求参数验证失败",
  429: "请求过于频繁，请稍后重试",
  500: "服务器内部错误，请稍后重试",
  502: "网关错误，服务可能正在重启",
  503: "服务暂时不可用，请稍后重试",
  504: "网关超时，请稍后重试",
};

export function getHttpStatusMessage(status) {
  const msg = HTTP_STATUS_MSG[status];
  return msg ? `${msg}（${status}）` : `请求失败（HTTP ${status}）`;
}

let _alertFn = null;
export function getAlert() {
  if (!_alertFn) {
    try {
      _alertFn = useAlertStore();
    } catch {
      _alertFn = null;
    }
  }
  return _alertFn;
}
```

- [ ] **Step 2: 修改 request.js**

删除 L14-45（`HTTP_STATUS_MSG` 定义和 `getHttpStatusMessage`/`_alert` 函数），替换为 import：

```js
// request.js — 删除原有定义，在顶部添加：
import { getHttpStatusMessage, getAlert } from "./constants";

// 同时：
// - L78-84: 将 `_alert()` 替换为 `getAlert()`
// - L90-98: 将 `_alert()` 替换为 `getAlert()`
```

- [ ] **Step 3: 修改 sse.js**

删除 L17-40（`HTTP_STATUS_MSG` 定义和 `_alert` 函数），替换为 import：

```js
// sse.js — 删除原有定义，在顶部添加：
import { HTTP_STATUS_MSG, getAlert } from "./constants";

// 同时：
// - L68: 将 `_alert()` 替换为 `getAlert()`
```

- [ ] **Step 4: 验证**

```bash
cd frontend && npm run build
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/constants.js frontend/src/api/request.js frontend/src/api/sse.js
git commit -m "refactor: extract HTTP_STATUS_MSG and alert helpers to api/constants.js"
```

---

### Task P1-6: 创建 useResizableDrawer.js composable

**Files:**
- Create: `frontend/src/composables/useResizableDrawer.js`

**Interfaces:**
- Produces:
  - `useResizableDrawer(options): { width, isResizing, startResize }`
  - options: `{ direction?: 'left'|'right', minWidth?: number, maxWidth?: number, defaultWidth?: number }`

- [ ] **Step 1: 创建 composable**

```js
// composables/useResizableDrawer.js
import { ref } from "vue";

export function useResizableDrawer(options = {}) {
  const {
    direction = "left",
    minWidth = 220,
    maxWidth = 700,
    defaultWidth = 320,
  } = options;

  const width = ref(defaultWidth);
  const isResizing = ref(false);

  function startResize(e) {
    e.preventDefault();
    isResizing.value = true;
    document.body.style.userSelect = "none";
    document.body.style.cursor = "col-resize";

    const startX = e.clientX;
    const startW = width.value;

    function onMove(ev) {
      const delta = direction === "left" ? ev.clientX - startX : startX - ev.clientX;
      width.value = Math.max(minWidth, Math.min(maxWidth, startW + delta));
    }

    function onUp() {
      isResizing.value = false;
      document.body.style.userSelect = "";
      document.body.style.cursor = "";
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
    }

    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  }

  return { width, isResizing, startResize };
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/composables/useResizableDrawer.js
git commit -m "feat: add useResizableDrawer composable"
```

---

### Task P1-7: 改造 ConversationsDrawer.vue 和 SettingsDrawer.vue

**Files:**
- Modify: `frontend/src/components/ConversationsDrawer.vue`
- Modify: `frontend/src/components/SettingsDrawer.vue`
- Create: `frontend/src/assets/drawer.css`

**Interfaces:**
- Consumes: `useResizableDrawer`
- 组件对外 props/emits 不变

- [ ] **Step 1: 创建 drawer.css 共享样式**

从两个 Drawer 组件中提取公共 CSS（`.drawer-panel`、`.drawer-resizer`、`.drawer-resizer.active`）：

```css
/* assets/drawer.css */
.drawer-panel {
  overflow: hidden;
  display: flex;
  flex-shrink: 0;
  transition: width 0.25s ease;
  position: relative;
}

.drawer-resizer {
  width: 4px;
  cursor: col-resize;
  flex-shrink: 0;
  background: transparent;
  transition: background 0.15s;
}
.drawer-resizer:hover,
.drawer-resizer.active {
  background: #4a90d9;
}
```

- [ ] **Step 2: 改造 ConversationsDrawer.vue**

将 L24-75 的 script 部分替换：

```vue
<script setup>
import { useResizableDrawer } from "@/composables/useResizableDrawer";
import { useChatStore } from "@/stores/chat";
import ConversationItem from "@/components/ConversationItem.vue";

defineProps({ visible: { type: Boolean, default: false } });
defineEmits(["close"]);

const chatStore = useChatStore();
const { width: drawerWidth, isResizing: resizing, startResize } = useResizableDrawer({
  direction: "left",
  minWidth: 220,
  maxWidth: 500,
  defaultWidth: 280,
});

function handleNewChat() {
  chatStore.createConversation();
}
</script>
```

模板中将 `drawerWidth` 引用改为 `drawerWidth`（已在 composable 中定义），`:class="{ active: resizing }"` 保持不变。

删除原有的 `drawerWidth`、`resizing` ref 定义和 `startResize` 函数。

在 `<style>` 中添加 `@import "@/assets/drawer.css";`，删除被 drawer.css 覆盖的重复样式。

- [ ] **Step 3: 改造 SettingsDrawer.vue**

```vue
<script setup>
import { useResizableDrawer } from "@/composables/useResizableDrawer";

defineProps({ visible: { type: Boolean, default: false } });
defineEmits(["close"]);

const { width: drawerWidth, isResizing: resizing, startResize } = useResizableDrawer({
  direction: "right",
  minWidth: 280,
  maxWidth: 700,
  defaultWidth: 420,
});
</script>
```

模板中将 `drawerWidth` 和 `startResize` 引用替换，删除原有 ref 定义和函数。

在 `<style>` 中添加 `@import "@/assets/drawer.css";`，删除重复样式。

- [ ] **Step 4: 验证**

```bash
cd frontend && npm run build
```

手动验证：两个 Drawer 的拖拽行为（方向、宽度限制）与改造前一致。

- [ ] **Step 5: P1 最终验证**

```bash
cd backend && python -m pytest -v   # 39 passed
cd frontend && npm run build        # 无错误
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/composables/useResizableDrawer.js \
        frontend/src/assets/drawer.css \
        frontend/src/components/ConversationsDrawer.vue \
        frontend/src/components/SettingsDrawer.vue
git commit -m "refactor: use useResizableDrawer in both Drawer components"
```

---

# 阶段三：P2（PR #3）— storage + stream + CRUD + http_client + chat.js

## 文件结构

```
新增:
  backend/app/storage/__init__.py
  backend/app/storage/conversations.py
  backend/app/storage/messages.py
  backend/app/storage/settings.py
  backend/app/services/stream_handler.py
  backend/app/services/http_client.py
  backend/app/routes/_helpers.py

删除:
  backend/app/storage.py

修改:
  backend/app/routes/conversations.py
  backend/app/routes/settings.py
  backend/app/services/ai.py
  backend/tests/conftest.py
  frontend/src/stores/chat.js
```

---

### Task P2-1: 拆分 storage — __init__.py + conversations.py

**Files:**
- Create: `backend/app/storage/__init__.py`
- Create: `backend/app/storage/conversations.py`

**Interfaces:**
- Produces (from __init__.py re-export):
  - `list_conversations() -> list`
  - `get_conversation(conv_id) -> dict|null`
  - `create_conversation(conv) -> None`
  - `update_conversation(conv_id, updates) -> None`
  - `delete_conversation(conv_id) -> None`

- [ ] **Step 1: 创建 storage/conversations.py**

从 `storage.py` 中提取 L1-108（导入、工具函数、init_storage、conversations CRUD）：

```python
# backend/app/storage/conversations.py
import json
import os
import threading

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, "user_data")
CONVERSATIONS_FILE = os.path.join(DATA_DIR, "conversations.json")
MESSAGES_DIR = os.path.join(DATA_DIR, "messages")

_lock = threading.Lock()

def _read_json(path, default=None):
    # 从 storage.py 完整复制
    pass

def _write_json(path, data):
    # 从 storage.py 完整复制
    pass

def init_storage():
    # 从 storage.py 完整复制
    pass

def list_conversations():
    # 从 storage.py L59-64 完整复制
    pass

def get_conversation(conv_id):
    # 从 storage.py L67-73 完整复制
    pass

def create_conversation(conv):
    # 从 storage.py L76-85 完整复制
    pass

def update_conversation(conv_id, updates):
    # 从 storage.py L88-96 完整复制
    pass

def delete_conversation(conv_id):
    # 从 storage.py L99-107 完整复制
    pass
```

> 注意：路径层级需要调整 —— 原 `storage.py` 在 `backend/app/`，新文件在 `backend/app/storage/`，多了一层 `os.path.dirname`。

- [ ] **Step 2: 创建 storage/__init__.py 重新导出**

```python
# backend/app/storage/__init__.py
from .conversations import (
    list_conversations, get_conversation, create_conversation,
    update_conversation, delete_conversation, init_storage,
    _read_json, _write_json, _lock, DATA_DIR, CONVERSATIONS_FILE, MESSAGES_DIR,
)
```

> 先只导出 conversations 部分，后续 task 追加 messages 和 settings。

- [ ] **Step 3: 验证路径正确性**

```bash
cd backend && python -c "from app.storage import list_conversations; print(list_conversations())"
```

确认无 ImportError，返回空列表 `[]`。

- [ ] **Step 4: Commit**

```bash
git add backend/app/storage/__init__.py backend/app/storage/conversations.py
git commit -m "refactor: extract conversations storage to submodule"
```

---

### Task P2-2: 拆分 storage — messages.py + settings.py

**Files:**
- Create: `backend/app/storage/messages.py`
- Create: `backend/app/storage/settings.py`
- Modify: `backend/app/storage/__init__.py`

**Interfaces:**
- Produces: messages 和 settings 的所有 CRUD 函数（函数签名与原 storage.py 完全一致）

- [ ] **Step 1: 创建 storage/messages.py**

从 `storage.py` L112-203 提取所有 messages 相关函数：

```python
# backend/app/storage/messages.py
import os
from .conversations import _read_json, _write_json, _lock, MESSAGES_DIR

def _msg_path(conv_id):
    return os.path.join(MESSAGES_DIR, f"{conv_id}.json")

def get_messages(conv_id):
    # 完整复制，import 来自 .conversations
    pass

def add_message(msg):
    # 完整复制
    pass

def get_message(msg_id, conv_id=None):
    # 完整复制
    pass

def update_message(msg_id, updates):
    # 完整复制
    pass

def delete_messages_after(conv_id, created_at):
    # 完整复制
    pass

def delete_message(msg_id, conv_id):
    # 完整复制
    pass

def get_last_assistant_message_id(conv_id):
    # 完整复制
    pass

def get_messages_for_chat(conv_id):
    # 完整复制
    pass
```

- [ ] **Step 2: 创建 storage/settings.py**

从 `storage.py` L208-274 提取所有 settings 相关函数：

```python
# backend/app/storage/settings.py
from .conversations import _read_json, _write_json, _lock, DATA_DIR
import os

SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

def _read_settings():
    return _read_json(SETTINGS_FILE)

def _write_settings(data):
    _write_json(SETTINGS_FILE, data)

def list_settings_raw():
    # 完整复制
    pass

def get_setting(setting_id):
    # 完整复制
    pass

def create_setting(s):
    # 完整复制
    pass

def update_setting(setting_id, updates):
    # 完整复制
    pass

def delete_setting(setting_id):
    # 完整复制
    pass

def get_default_setting():
    # 完整复制
    pass

def set_default_setting(setting_id):
    # 完整复制
    pass
```

- [ ] **Step 3: 更新 __init__.py 追加导出**

```python
# backend/app/storage/__init__.py
from .conversations import (
    list_conversations, get_conversation, create_conversation,
    update_conversation, delete_conversation, init_storage,
)

from .messages import (
    get_messages, add_message, get_message, update_message,
    delete_messages_after, delete_message, get_last_assistant_message_id,
    get_messages_for_chat,
)

from .settings import (
    list_settings_raw, get_setting, create_setting,
    update_setting, delete_setting, get_default_setting, set_default_setting,
)
```

- [ ] **Step 4: 删除原 storage.py 并验证**

```bash
rm backend/app/storage.py
cd backend && python -m pytest -v
```

预期：所有测试仍通过（如果 conftest.py 中有 `monkeypatch` 指向 `app.storage.*`，路径应自动适配因为 `__init__.py` 重新导出了相同名称）。

如果测试失败，检查 conftest.py 是否需要调整（通常不需要，因为 `from app.storage import xxx` 仍有效）。

- [ ] **Step 5: Commit**

```bash
git add backend/app/storage/messages.py backend/app/storage/settings.py \
        backend/app/storage/__init__.py backend/app/storage.py
git commit -m "refactor: finish storage split — messages + settings submodules"
```

---

### Task P2-3: 创建 services/http_client.py

**Files:**
- Create: `backend/app/services/http_client.py`

**Interfaces:**
- Produces:
  - `api_post(url, headers, json, timeout=30) -> (data, error)`
  - `api_get(url, headers, timeout=10) -> (data, error)`

- [ ] **Step 1: 创建 http_client.py**

```python
# backend/app/services/http_client.py
import requests

def api_post(url, headers, json, timeout=30):
    """统一的 JSON POST 请求。返回 (response_json, error_string)。"""
    try:
        resp = requests.post(url, headers=headers, json=json, timeout=timeout)
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return None, str(e)

def api_get(url, headers, timeout=10):
    """统一的 JSON GET 请求。返回 (response_json, error_string)。"""
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return None, str(e)
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/http_client.py
git commit -m "feat: add unified HTTP client for API calls"
```

---

### Task P2-4: 改造 settings.py 使用 http_client

**Files:**
- Modify: `backend/app/routes/settings.py`

**Interfaces:**
- Consumes: `api_post`, `api_get` from `services/http_client.py`
- 路由签名和行为不变

- [ ] **Step 1: 改造 test_setting 路由**

原代码中 `test_setting` 函数（约 L139-152）的 `try: requests.post → except → fail(502)` 替换为：

```python
from app.services.http_client import api_post, api_get

@api_bp.route("/settings/test", methods=["POST"])
def test_setting():
    data = request.get_json() or {}
    url = data.get("api_url", "").rstrip("/") + "/models"
    api_key = data.get("api_key", "")

    resp_data, error = api_get(url, headers={"Authorization": f"Bearer {api_key}"})
    if error:
        return fail(502, f"连接测试失败: {error}", request)

    return ok(resp_data, "连接成功")
```

- [ ] **Step 2: 改造 fetch_models 路由**

同理替换 `fetch_models` 中的 `requests.get` 调用：

```python
@api_bp.route("/settings/models", methods=["POST"])
def fetch_models():
    data = request.get_json() or {}
    url = data.get("api_url", "").rstrip("/") + "/models"
    api_key = data.get("api_key", "")

    resp_data, error = api_get(url, headers={"Authorization": f"Bearer {api_key}"})
    if error:
        return fail(502, f"获取模型列表失败: {error}", request)

    return ok(resp_data, "获取成功")
```

- [ ] **Step 3: 验证**

```bash
cd backend && python -m pytest tests/ -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/routes/settings.py
git commit -m "refactor: use http_client in settings routes"
```

---

### Task P2-5: 改造 ai.py 使用 http_client

**Files:**
- Modify: `backend/app/services/ai.py`

**Interfaces:**
- Consumes: `api_post` from `services/http_client.py`
- `stream_chat` 函数签名不变

- [ ] **Step 1: 改造 stream_chat**

将 `ai.py` 中 `stream_chat` 函数的 `requests.post(..., stream=True)` 调用改为使用 `api_post`（但注意 `stream=True` 场景需要保留原生 requests，因为需要迭代 SSE 流）。

**重要**：`stream_chat` 需要 `stream=True` 来逐 token 读取响应，`api_post` 不支持流式。处理方式：

在 `ai.py` 中仅对可抽取的重复错误处理逻辑做统一，保留 `stream=True` 的原始调用：

```python
# services/ai.py
import requests
from app.services.http_client import api_post

def stream_chat(messages, setting):
    url = setting["api_url"].rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {setting['api_key']}",
        "Content-Type": "application/json",
    }
    body = {
        "model": setting.get("model", "gpt-3.5-turbo"),
        "messages": messages,
        "stream": True,
    }
    try:
        resp = requests.post(url, headers=headers, json=body, stream=True, timeout=120)
        resp.raise_for_status()
        # ... 迭代 SSE chunks
    except requests.RequestException as e:
        yield {"error": str(e)}
```

> 由于 `stream=True` 场景与普通 JSON 请求差异较大，保持原生 `requests` 调用是合理的。此 task 的主要价值是将 `settings.py` 中的重复模式消除；`ai.py` 改动最小化、不强行统一。

- [ ] **Step 2: 验证**

```bash
cd backend && python -m pytest tests/ -v
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/ai.py
git commit -m "refactor: minor cleanup in ai.py, http_client used where applicable"
```

---

### Task P2-6: 创建 services/stream_handler.py

**Files:**
- Create: `backend/app/services/stream_handler.py`

**Interfaces:**
- Produces:
  - `stream_and_save(conv_id, messages, setting, sse_manager) -> generator`
  - 生成器 yield: `{delta?, reasoning_delta?, done?, stopped?, error?}`

- [ ] **Step 1: 创建 stream_handler.py**

从 `routes/conversations.py` 的 `_stream_and_save` 函数中提取完整逻辑：

```python
# backend/app/services/stream_handler.py
from app.services.ai import stream_chat
from app.storage import add_message
from app.services.sse_manager import get_sse_manager

sse_manager = get_sse_manager()

def stream_and_save(conv_id, messages, setting, user_content, assistant_msg_id):
    """生成器：逐 token yield SSE chunk，完成后持久化到存储。"""
    full_content = ""
    reasoning_content = ""

    try:
        for chunk in stream_chat(messages, setting):
            if sse_manager.is_cancelled(conv_id):
                sse_manager.unregister(conv_id)
                yield {"stopped": True}
                return

            if "error" in chunk:
                yield {"error": chunk["error"]}
                break

            delta = chunk.get("delta", "")
            reasoning_delta = chunk.get("reasoning_delta", "")
            done = chunk.get("done", False)

            if reasoning_delta:
                reasoning_content += reasoning_delta
            if delta:
                full_content += delta

            yield chunk

            if done:
                break

        # 流结束 → 持久化
        from app.storage import add_message
        import datetime

        user_msg = {
            "id": f"user-{conv_id}-{int(datetime.datetime.now().timestamp() * 1000)}",
            "conversation_id": conv_id,
            "role": "user",
            "content": user_content,
            "created_at": datetime.datetime.now().isoformat(),
        }
        add_message(user_msg)

        assistant_msg = {
            "id": assistant_msg_id,
            "conversation_id": conv_id,
            "role": "assistant",
            "content": full_content,
            "reasoning_content": reasoning_content,
            "created_at": datetime.datetime.now().isoformat(),
        }
        add_message(assistant_msg)

    finally:
        sse_manager.unregister(conv_id)
```

> 注意：消息 ID 生成和持久化逻辑需与当前 `_stream_and_save` 实现一致，以源文件为准微调。

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/stream_handler.py
git commit -m "refactor: extract stream_and_save to services/stream_handler.py"
```

---

### Task P2-7: 精简 routes/conversations.py

**Files:**
- Modify: `backend/app/routes/conversations.py`

**Interfaces:**
- Consumes: `stream_and_save` from `services/stream_handler.py`
- 路由签名不变

- [ ] **Step 1: 替换 _stream_and_save**

删除 `_stream_and_save` 函数定义（L27-70 区域），将 chat 路由改为调用 `stream_handler.stream_and_save`：

```python
from app.services.stream_handler import stream_and_save

@api_bp.route("/conversations/<conv_id>/chat", methods=["POST"])
def chat(conv_id):
    # ... 参数提取逻辑不变 ...
    return Response(
        stream_with_context(stream_and_save(conv_id, messages, setting, content, assistant_msg_id)),
        mimetype="text/event-stream",
    )
```

- [ ] **Step 2: 验证**

```bash
cd backend && python -m pytest tests/ -v
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routes/conversations.py
git commit -m "refactor: delegate stream logic to services/stream_handler"
```

---

### Task P2-8: 提取 routes/_helpers.py CRUD 辅助

**Files:**
- Create: `backend/app/routes/_helpers.py`
- Modify: `backend/app/routes/conversations.py`
- Modify: `backend/app/routes/settings.py`

**Interfaces:**
- Produces:
  - `get_or_404(fetcher, id, name="资源") -> (row, error_response)`

- [ ] **Step 1: 创建 _helpers.py**

```python
# backend/app/routes/_helpers.py
from app.utils.response import fail

def get_or_404(fetcher, id, name="资源"):
    """通用「取或404」守卫。返回 (row, error_response)。"""
    row = fetcher(id)
    if not row:
        return None, fail(404, f"{name}不存在")
    return row, None
```

- [ ] **Step 2: 改造 conversations.py**

逐一替换路由中的 `not conv → fail(404)` 模式：

```python
from ._helpers import get_or_404

# 示例：update 路由
conv, err = get_or_404(get_conversation, conv_id, "会话")
if err:
    return err
```

同理替换其他路由的 get/update/delete 守卫。

- [ ] **Step 3: 改造 settings.py**

同理：

```python
from ._helpers import get_or_404

setting, err = get_or_404(get_setting, setting_id, "设置")
if err:
    return err
```

- [ ] **Step 4: 验证**

```bash
cd backend && python -m pytest tests/ -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/routes/_helpers.py \
        backend/app/routes/conversations.py \
        backend/app/routes/settings.py
git commit -m "refactor: extract get_or_404 helper for CRUD routes"
```

---

### Task P2-9: 优化 stores/chat.js

**Files:**
- Modify: `frontend/src/stores/chat.js`

**Interfaces:**
- 对外暴露的 state/actions 不变
- 新增内部 getter `sortedConversations`
- 新增内部辅助函数 `applyChunk`

- [ ] **Step 1: 添加 getter 消除排序重复**

在 store 定义中添加 getter：

```js
export const useChatStore = defineStore("chat", {
  state: () => ({ /* ... 不变 ... */ }),

  getters: {
    sortedConversations: (state) =>
      [...state.conversations].sort((a, b) =>
        (b.lastMessageAt || "").localeCompare(a.lastMessageAt || "")
      ),
  },
  // ...
});
```

然后 `loadConversations` 中：
```js
// 旧：this.conversations.sort(...)
// 新：删除 sort 调用，转为依赖 getter（如果 conversations 被直接引用需改造）
```

> 注意：由于 `conversations` 在模板中可能直接用 `chatStore.conversations`，需要检查是否需要改为 `chatStore.sortedConversations`。如果改动范围大，可暂时保留 sort 在 actions 中的显式调用，仅添加 getter 供未来迁移。

- [ ] **Step 2: 提取 applyChunk 辅助函数**

在 store 外部（文件顶部或 actions 上方）定义：

```js
function applyChunk(msg, chunk) {
  if (chunk.reasoning_delta) {
    msg.reasoning_content = (msg.reasoning_content || "") + chunk.reasoning_delta;
  }
  if (chunk.delta) {
    msg.content = (msg.content || "") + chunk.delta;
  }
  if (chunk.done || chunk.stopped) {
    msg.streaming = false;
  }
}
```

改造 `sendMessage` 的 `onMessage`（L107-127）：

```js
onMessage: (chunk) => {
  if (chunk.stopped) {
    this.isStreaming = false;
    return;
  }
  const last = this.messages[this.messages.length - 1];
  if (last && last.role === "assistant") {
    applyChunk(last, chunk);
  }
  if (chunk.done) {
    this.isStreaming = false;
  }
},
```

改造 `replayMessage` 的 `onMessage`（L183-202）：

```js
onMessage: (chunk) => {
  if (chunk.stopped) {
    this.isStreaming = false;
    return;
  }
  if (chunk.reasoning_delta) {
    newReasoning.value += chunk.reasoning_delta;
    assistantMsg.reasoning_content = newReasoning.value;
  }
  if (chunk.delta) {
    newContent.value += chunk.delta;
    assistantMsg.content = newContent.value;
  }
  if (chunk.done) {
    assistantMsg.reasoning_content = newReasoning.value;
    this.aiVersions[id].push(newContent.value);
    this.aiVersionIndex = this.aiVersions[id].length - 1;
    this.isStreaming = false;
  }
},
```

> `replayMessage` 的 chunk 处理使用了 `newContent.value` 和 `newReasoning.value` 作为中间变量（因为需要版本管理），结构上不同于 `sendMessage` 的直接 `this.messages[last]` 操作，不适合直接用 `applyChunk`。此处仅对 `sendMessage` 精简。

- [ ] **Step 3: 验证**

```bash
cd frontend && npm run build
cd backend && python -m pytest -v
```

- [ ] **Step 4: P2 最终验证**

```bash
cd backend && python -m pytest -v   # 39 passed
cd frontend && npm run build        # 无错误

# 手动回归：
# - 会话 CRUD（创建/选择/删除/重命名）
# - 消息发送/流式接收/停止生成
# - 消息重生成/版本切换
# - 设置 CRUD/连通性测试/模型列表
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/stores/chat.js
git commit -m "refactor: extract applyChunk helper and sortedConversations getter in chat store"
```

---

## 验证摘要

| 阶段 | 自动化 | 手动 |
|------|--------|------|
| P0 | `pytest` 39 passed + `npm run build` | 弹窗交互验证 |
| P1 | `pytest` 39 passed + `npm run build` | Markdown 渲染 + Drawer 拖拽 |
| P2 | `pytest` 39 passed + `npm run build` | 完整功能回归 + `electron:build` |
