# API 设置页面重设计 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 API 设置页面改为分组卡片式布局，新建 tokens.css 集中管理设计变量，新增状态指示行和自动连接开关，重设计测试按钮。

**Architecture:** 新建 `tokens.css` 存放全部 CSS 变量，`App.vue` 改为 `@import` 引用。`SettingsView.vue` 重写为 4 张卡片 + 状态行 + 紧凑按钮。`PresetSelector`/`ModelSelector`/`ResponseFormatInput` 三个子组件仅改样式（硬编码→变量）。`settings.js` store 新增 `autoConnect` 和 `connectionStatus`。

**Tech Stack:** Vue 3 (Composition API), Pinia, CSS Variables, Lucide Vue Next

## Global Constraints

- 所有颜色通过 CSS 变量引用，不硬编码（`tokens.css` 为唯一来源）
- 表单控件统一：`bg: var(--bg-input)`, `border: var(--border-light)`, `radius: var(--radius-sm)=8px`
- focus 态统一：`border-color: var(--accent)` + `box-shadow: var(--focus-ring)`
- disabled 统一 `opacity: 0.45`
- 卡片边框 `var(--border)`, 圆角 `var(--radius-lg)=16px`, 阴影 `var(--shadow-xs)`
- 测试按钮：`inline-flex`, 不拉伸全宽
- 反馈：测试结果用内联消息 + 状态指示行，错误用 AlertDialog 弹窗
- 不在此范围：`BaseDialog.vue`、后端 API、CSS 预设系统

---

### Task 1: 新建 tokens.css + 迁移 App.vue 变量

**Files:**
- Create: `frontend/src/assets/tokens.css`
- Modify: `frontend/src/App.vue`

**Interfaces:**
- Produces: 全部设计 Token 变量，供后续所有组件引用

- [ ] **Step 1: 创建 tokens.css**

```css
/* 背景 */
--bg-primary: #fff;
--bg-secondary: #f8f9fb;
--bg-tertiary: #f0f1f5;
--bg-input: #fafbfc;
--bg-input-hover: #f0f1f5;

/* 文字 */
--text-primary: #1a1a2e;
--text-secondary: #5b5b7a;
--text-muted: #8e8ea0;

/* 边框 */
--border: #e2e4eb;
--border-light: #d8dae2;

/* 强调色 */
--accent: #4f6ef6;
--accent-light: #6c8cfc;
--accent-bg: rgba(79,110,246,0.08);

/* 语义色 */
--danger: #ef4444;
--danger-bg: #fef2f2;
--success: #2e7d32;
--success-bg: #f0faf0;
--success-border: #c8e6c9;
--error-text: #991b1b;
--error-bg: #fef2f2;
--error-border: #fecaca;

/* 阴影 */
--shadow-xs: 0 1px 2px rgba(0,0,0,0.04);
--shadow-sm: 0 2px 8px rgba(0,0,0,0.06);
--shadow-md: 0 4px 16px rgba(0,0,0,0.08);
--shadow-lg: 0 8px 32px rgba(0,0,0,0.10);

/* 玻璃态 */
--glass-bg: rgba(255,255,255,0.7);
--glass-border: rgba(0,0,0,0.06);
--glass-blur: 12px;

/* 圆角 */
--radius-sm: 8px;
--radius-md: 10px;
--radius-lg: 16px;
--radius-xl: 28px;

/* 聚焦环 */
--focus-ring: 0 0 0 3px rgba(79,110,246,0.1);

/* API 设置页面专用 */
--card-icon-color: var(--accent);
--test-btn-bg: var(--accent);
--test-btn-text: #fff;
--status-dot-disconnected: #ccc;
--status-dot-connected: #22c55e;
--toggle-bg-off: #e2e4eb;
--toggle-bg-on: var(--accent);
```

写入文件 `frontend/src/assets/tokens.css`，包裹在 `:root { ... }` 中。

- [ ] **Step 2: 修改 App.vue — 替换 :root 块为 @import**

在 App.vue 的非 scoped `<style>` 块中，将现有的 `:root { ... }` 块（第 104-127 行）替换为：

```css
@import "@/assets/tokens.css";
```

确保该行在其他样式规则之前。

- [ ] **Step 3: 验证构建**

```bash
cd frontend
npx vite build --mode development 2>&1 | tail -3
```

Expected: `✓ built in ...`，无 CSS 错误。

- [ ] **Step 4: Commit**

```bash
git add frontend/src/assets/tokens.css frontend/src/App.vue
git commit -m "refactor: extract CSS tokens to tokens.css, import in App.vue"
```

---

### Task 2: 重写 SettingsView.vue — 卡片式布局 + 状态行 + 自动连接

**Files:**
- Modify: `frontend/src/views/SettingsView.vue`

**Interfaces:**
- Consumes: `tokens.css` 变量, `settingsStore`, `PresetSelector`, `ModelSelector`, `ResponseFormatInput`
- Produces: 卡片式布局页面, 暴露 `connectionStatus` / `autoConnect` 给状态指示行

- [ ] **Step 1: 重写模板**

```vue
<template>
  <div class="settings-page">
    <!-- 卡片1: 预设管理 -->
    <div class="card">
      <div class="card-header">
        <span class="card-icon"><Settings :size="18" /></span>
        <span class="card-label">预设</span>
      </div>
      <PresetSelector />
    </div>

    <!-- 卡片2: 连接信息 -->
    <div class="card">
      <div class="card-header">
        <span class="card-icon"><Plug :size="18" /></span>
        <span class="card-label">连接信息</span>
      </div>
      <div class="form-row">
        <span class="field-label">API URL</span>
        <input v-model="store.apiUrl" class="input-field input-mono" placeholder="https://api.openai.com/v1" />
      </div>
      <div class="form-row">
        <span class="field-label">API Key</span>
        <input v-model="store.apiKey" class="input-field input-mono" type="password" placeholder="sk-···" />
      </div>
    </div>

    <!-- 卡片3: 模型 -->
    <div class="card">
      <div class="card-header">
        <span class="card-icon"><MessageSquare :size="18" /></span>
        <span class="card-label">模型</span>
      </div>
      <ModelSelector />
    </div>

    <!-- 卡片4: 响应格式 -->
    <div class="card">
      <div class="card-header">
        <span class="card-icon"><Code :size="18" /></span>
        <span class="card-label">响应格式</span>
      </div>
      <ResponseFormatInput />
    </div>

    <!-- 状态指示行 -->
    <div class="status-bar">
      <div class="status-left">
        <span class="status-dot" :class="store.connectionStatus"></span>
        <span class="status-text" :class="{ connected: store.connectionStatus === 'connected' }">
          {{ statusLabel }}
        </span>
      </div>
      <div class="auto-connect-toggle" @click="store.autoConnect = !store.autoConnect">
        <div class="toggle-box" :class="{ on: store.autoConnect }">
          <svg v-if="store.autoConnect" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
        </div>
        <span class="toggle-label">自动连接</span>
      </div>
    </div>

    <!-- 测试按钮 -->
    <div class="test-section">
      <button class="test-btn" :disabled="testing || !store.apiUrl || !store.apiKey" @click="handleTestConnection">
        <span v-if="testing" class="btn-spinner"></span>
        <RefreshCw v-else :size="15" />
        {{ testing ? '测试中...' : (store.connectionStatus === 'connected' ? '重新测试' : '测试连接') }}
      </button>
    </div>
  </div>
</template>
```

- [ ] **Step 2: 重写 script**

```vue
<script setup>
import { ref, computed, onMounted } from "vue";
import { Settings, Plug, MessageSquare, Code, RefreshCw } from "lucide-vue-next";
import { useSettingsStore } from "@/stores/settings";
import { useAlertStore } from "@/stores/alert";
import PresetSelector from "@/components/PresetSelector.vue";
import ModelSelector from "@/components/ModelSelector.vue";
import ResponseFormatInput from "@/components/ResponseFormatInput.vue";

const store = useSettingsStore();
const alert = useAlertStore();
const testing = ref(false);

const statusLabel = computed(() => {
  switch (store.connectionStatus) {
    case "testing": return "正在测试连接...";
    case "connected": return `已连接 · ${store.availableModels.length} 个模型可用`;
    default: return "未连接";
  }
});

onMounted(async () => {
  try { await store.loadPresets(); } catch (e) { console.error("加载预设失败:", e); }
  // 自动连接
  if (store.autoConnect && store.apiUrl && store.apiKey) {
    handleTestConnection();
  }
});

async function handleTestConnection() {
  testing.value = true;
  store.connectionStatus = "testing";
  try {
    await store.fetchModels();
    store.connectionStatus = "connected";
  } catch (e) {
    store.connectionStatus = "disconnected";
    alert.error("连接失败", e.message || "请检查 API URL 和 Key 是否正确");
  } finally {
    testing.value = false;
  }
}
</script>
```

关键变更：移除 `testResult` ref，改为 `store.connectionStatus` 驱动状态指示行；新增 `autoConnect` 启动自动测试；引入 Lucide 图标替代纯文字标签。

- [ ] **Step 3: 重写样式（非 scoped）**

```css
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ——— 卡片 ——— */
.card {
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
}
.card-header {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 12px;
}
.card-icon {
  color: var(--card-icon-color);
  display: flex; align-items: center; justify-content: center;
  width: 20px; height: 20px;
}
.card-label {
  font-size: 13px; font-weight: 600;
  color: var(--text-secondary);
}

/* ——— 表单控件 ——— */
.form-row {
  display: flex; flex-direction: column; gap: 4px;
  margin-bottom: 10px;
}
.form-row:last-child { margin-bottom: 0; }
.field-label {
  font-size: 11px; font-weight: 500;
  color: var(--text-muted);
  text-transform: uppercase; letter-spacing: 0.3px;
}
.input-field {
  width: 100%; padding: 8px 12px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  font-size: 13px; color: var(--text-primary);
  background: var(--bg-input); outline: none;
  font-family: inherit;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.input-field:focus {
  border-color: var(--accent);
  box-shadow: var(--focus-ring);
}
.input-field::placeholder { color: var(--text-muted); }
.input-mono {
  font-family: "Consolas", "Monaco", monospace; font-size: 12px;
}

/* ——— 状态指示行 ——— */
.status-bar {
  display: flex; align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: var(--bg-input);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  gap: 12px;
}
.status-left {
  display: flex; align-items: center; gap: 8px;
}
.status-dot {
  width: 8px; height: 8px;
  border-radius: 50%; flex-shrink: 0;
  transition: background 0.3s;
}
.status-dot.disconnected { background: var(--status-dot-disconnected); }
.status-dot.connected { background: var(--status-dot-connected); }
.status-dot.testing {
  background: var(--accent);
  animation: pulse-dot 1s ease-in-out infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.7); }
}
.status-text {
  font-size: 12px; color: var(--text-secondary);
  white-space: nowrap;
}
.status-text.connected { color: var(--success); font-weight: 500; }

/* ——— 自动连接开关 ——— */
.auto-connect-toggle {
  display: flex; align-items: center; gap: 6px;
  cursor: pointer; user-select: none; flex-shrink: 0;
}
.toggle-box {
  width: 18px; height: 18px;
  border: 2px solid var(--border-light);
  border-radius: 4px;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s;
  background: var(--bg-input);
}
.toggle-box.on {
  background: var(--toggle-bg-on);
  border-color: var(--toggle-bg-on);
}
.toggle-label {
  font-size: 12px; color: var(--text-muted);
  transition: color 0.15s;
}
.auto-connect-toggle:hover .toggle-label { color: var(--text-secondary); }
.auto-connect-toggle:hover .toggle-box:not(.on) { border-color: var(--border); }

/* ——— 测试按钮 ——— */
.test-section {
  display: flex; align-items: center; gap: 12px;
}
.test-btn {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 8px 18px;
  border: none; border-radius: var(--radius-sm);
  background: var(--test-btn-bg); color: var(--test-btn-text);
  font-size: 13px; font-weight: 600;
  cursor: pointer; font-family: inherit;
  transition: background 0.15s, transform 0.15s, box-shadow 0.15s;
  box-shadow: 0 1px 3px rgba(79,110,246,0.2);
}
.test-btn:hover:not(:disabled) {
  background: var(--accent-light);
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(79,110,246,0.3);
}
.test-btn:disabled {
  opacity: 0.45; cursor: default; transform: none; box-shadow: none;
}
.btn-spinner {
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
```

样式全部放入非 scoped `<style>` 块供自定义 CSS 覆盖。

- [ ] **Step 4: 验证构建**

```bash
cd frontend
npx vite build --mode development 2>&1 | tail -3
```

Expected: `✓ built in ...`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/SettingsView.vue
git commit -m "feat: redesign API settings with card layout, status bar, auto-connect"
```

---

### Task 3: 更新 settings store（autoConnect + connectionStatus）

**Files:**
- Modify: `frontend/src/stores/settings.js`

**Interfaces:**
- Consumes: 被 SettingsView.vue 消费
- Produces: `autoConnect: boolean`, `connectionStatus: 'disconnected' | 'testing' | 'connected'`

- [ ] **Step 1: 在 state 中添加两个字段**

在 `state` 中（`availableModels: []` 之后）增加：

```js
autoConnect: false,
connectionStatus: "disconnected", // 'disconnected' | 'testing' | 'connected'
```

- [ ] **Step 2: 验证构建**

```bash
cd frontend
npx vite build --mode development 2>&1 | tail -3
```

Expected: `✓ built in ...`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/stores/settings.js
git commit -m "feat: add autoConnect and connectionStatus to settings store"
```

---

### Task 4: 统一子组件样式（PresetSelector / ModelSelector / ResponseFormatInput）

**Files:**
- Modify: `frontend/src/components/PresetSelector.vue`
- Modify: `frontend/src/components/ModelSelector.vue`
- Modify: `frontend/src/components/ResponseFormatInput.vue`

**Interfaces:**
- Consumes: `tokens.css` 变量
- Produces: 样式变量化，统一 focus 环、border-radius、disabled opacity

- [ ] **Step 1: 修改 PresetSelector.vue 样式**

将 `<style scoped>` 中的硬编码颜色全部替换为 CSS 变量。完整替换如下：

```css
.preset-area { position: relative; }
.preset-row { display: flex; gap: 6px; align-items: center; }

.preset-select {
  flex: 1; padding: 7px 10px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  font-size: 13px; color: var(--text-primary);
  background: var(--bg-input); outline: none;
  font-family: inherit; cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.preset-select:focus {
  border-color: var(--accent);
  box-shadow: var(--focus-ring);
}

.preset-btn {
  width: 32px; height: 32px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  background: var(--bg-input); color: var(--text-secondary);
  cursor: pointer; display: flex; align-items: center;
  justify-content: center; flex-shrink: 0;
  transition: all 0.15s;
}
.preset-btn:hover:not(:disabled) {
  color: var(--text-primary);
  border-color: var(--border);
  background: var(--bg-input-hover);
}
.preset-btn:disabled { opacity: 0.45; cursor: default; }

.preset-toast {
  position: absolute; top: -28px; left: 0;
  font-size: 12px; color: var(--text-secondary);
  background: var(--bg-input); padding: 3px 10px;
  border-radius: var(--radius-sm); white-space: nowrap;
  pointer-events: none;
}
.fade-enter-active, .fade-leave-active { transition: opacity 0.25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
```

关键变更：`border-radius: 6px` → `var(--radius-sm)`=8px、`opacity: 0.3` → `0.45`、select 新增 focus 样式、颜色全部变量化。

- [ ] **Step 2: 修改 ModelSelector.vue 样式**

```css
.model-row { display: flex; gap: 6px; align-items: center; }

.model-select {
  flex: 1; padding: 7px 10px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  font-size: 13px; color: var(--text-primary);
  background: var(--bg-input); outline: none;
  font-family: inherit; cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.model-select:focus {
  border-color: var(--accent);
  box-shadow: var(--focus-ring);
}

.fetch-btn {
  height: 32px; padding: 0 10px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  background: var(--bg-input); color: var(--text-secondary);
  cursor: pointer; font-size: 12px;
  display: flex; align-items: center; gap: 5px;
  transition: all 0.15s; font-family: inherit;
}
.fetch-btn:hover:not(:disabled) {
  color: var(--text-primary);
  border-color: var(--border);
  background: var(--bg-input-hover);
}
.fetch-btn:disabled { opacity: 0.45; cursor: default; }

.spinning { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
```

关键变更：`fetch-btn` 从 32×32 正方改为 `height:32px; padding:0 10px` 文字按钮（含"拉取"文字）、`border-radius: 6px` → `var(--radius-sm)`、`opacity: 0.3` → `0.45`、select 新增 focus。

同时更新模板中 `fetch-btn` 的文字。当前只有 SVG 图标，需增加"拉取"文字：

```diff
- <button class="fetch-btn" title="拉取模型列表" @click="handleFetch" :disabled="fetching">
+ <button class="fetch-btn" @click="handleFetch" :disabled="fetching">
    <svg ... :class="{ spinning: fetching }">...</svg>
+   拉取
  </button>
```

- [ ] **Step 3: 修改 ResponseFormatInput.vue 样式**

```css
.resp-format-input {
  width: 100%; min-height: 90px;
  padding: 10px 12px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  font-size: 12px; color: var(--text-primary);
  background: var(--bg-input); outline: none;
  resize: vertical; line-height: 1.5;
  font-family: "Consolas", "Monaco", monospace;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.resp-format-input:focus {
  border-color: var(--accent);
  box-shadow: var(--focus-ring);
}
.resp-format-input::placeholder { color: var(--text-muted); }
```

关键变更：`height: 150px` → `min-height: 90px`、focus 从 `#aaa` 改为 accent 色 + focus-ring、颜色变量化。

- [ ] **Step 4: 验证构建**

```bash
cd frontend
npx vite build --mode development 2>&1 | tail -3
```

Expected: `✓ built in ...`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/PresetSelector.vue frontend/src/components/ModelSelector.vue frontend/src/components/ResponseFormatInput.vue
git commit -m "style: use CSS variables in API settings child components, unify focus/border-radius"
```

---

### Task 5: 端到端验证

**Files:**
- 无

- [ ] **Step 1: 启动开发服务器**

```bash
cd frontend
npx vite --host 127.0.0.1 &
sleep 3
```

- [ ] **Step 2: 手动验证清单**

在浏览器打开 `http://127.0.0.1:5173`，打开 API 设置抽屉：

| # | 检查项 | 预期 |
|---|--------|------|
| 1 | 4 张卡片可见（预设/连接/模型/响应格式），每张有 accent 色 SVG 图标 | ✅ |
| 2 | 表单控件浅灰底 `#fafbfc`，focus 时蓝边框 + 发光环 | ✅ |
| 3 | 状态指示行在卡片下方，默认灰点 + "未连接" | ✅ |
| 4 | 自动连接开关可点击切换，开启时蓝色方块 + 白色对号 | ✅ |
| 5 | 输入 URL + Key 后测试按钮可用，点击后圆点变蓝脉冲 + "正在测试连接..." | ✅ |
| 6 | 测试成功后圆点变绿 + "已连接 · N 个模型可用"，按钮文字变"重新测试" | ✅ |
| 7 | 测试失败弹 AlertDialog，圆点恢复灰色 | ✅ |
| 8 | 预设操作按钮 hover 变深，删除按钮 hover 变红 | ✅ |
| 9 | 拉取按钮含"拉取"文字 + 刷新图标 | ✅ |
| 10 | 缩小窗口，按钮不溢出，卡片自适应 | ✅ |

- [ ] **Step 3: 停止服务器并提交（如有修正）**

```bash
kill %1 2>/dev/null
```

---

### Task 6: 最终构建验证

**Files:**
- 无

- [ ] **Step 1: 生产构建**

```bash
cd frontend
npx vite build 2>&1 | tail -5
```

Expected: `✓ built in ...`

- [ ] **Step 2: 清理临时文件并提交文档**

```bash
rm -rf temp_api_preview
git add docs/superpowers/specs/2026-07-27-api-settings-redesign.md docs/superpowers/plans/2026-07-27-api-settings-redesign.md
git commit -m "docs: add API settings redesign spec and implementation plan"
```

- [ ] **Step 3: 最终状态确认**

```bash
git status
```
