# 顶部工具栏图标化 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将顶部工具栏 5 个文字按钮替换为纯 SVG 图标按钮（Lucide），激活态通过底部 accent 色下划线指示。

**Architecture:** 单文件改动 `App.vue`，用 `lucide-vue-next` 的 5 个图标组件替换现有 `<button>文字</button>` 和 `<CssPresetSelector>`，复用现有 `.top-btn` 样式体系，新增 `.top-btn.active` 激活态规则。

**Tech Stack:** Vue 3 (Composition API), Lucide Vue Next, CSS Variables, Vite

## Global Constraints

- 仅修改 `frontend/src/App.vue`（模板 + 样式 + script imports）
- 安装依赖：`lucide-vue-next`（npm 包，MIT 协议，Tree-shakable）
- 颜色全部使用 CSS 变量（`--text-secondary`、`--text-primary`、`--accent`），不硬编码
- 按钮 36×36px 正方，图标 18×18px
- 激活态 = 底部 2px accent 下划线 width:100% + 图标颜色 text-primary
- 原生 `title` 属性作 tooltip，不引入额外组件
- "会话记录" 的 `showConversations` 独立于右侧 `activeDrawer` 互斥逻辑
- 移除 `CssPresetSelector` 组件引用后可安全删除该文件

---

### Task 1: 安装 lucide-vue-next 依赖

**Files:**
- Modify: `frontend/package.json`（npm install 自动更新）

- [ ] **Step 1: 安装 lucide-vue-next**

```bash
cd frontend
npm install lucide-vue-next
```

- [ ] **Step 2: 验证安装**

```bash
node -e "const m = require('lucide-vue-next'); console.log(Object.keys(m).slice(0,5))"
```

Expected: 输出 `[ 'createIcons', 'Accessibility', 'Activity', 'AirVent', 'AlarmClock' ]` 等

- [ ] **Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "chore: install lucide-vue-next for toolbar icons"
```

---

### Task 2: 更新 App.vue — 模板与 Script

**Files:**
- Modify: `frontend/src/App.vue`（template 区域和 script imports）

**Interfaces:**
- Consumes: `lucide-vue-next` 的 5 个图标组件
- Produces: 图标按钮替代原文字按钮，每个带 `:class="{ active: ... }"` 和 `title`

- [ ] **Step 1: 修改 script import 部分**

将现有 imports（第 42-51 行）中移除 `CssPresetSelector`，新增 5 个 Lucide 图标组件：

```js
import { ref, computed, onMounted } from "vue";
import ConversationsDrawer from "@/components/ConversationsDrawer.vue";
import SettingsDrawer from "@/components/SettingsDrawer.vue";
import SettingsView from "@/views/SettingsView.vue";
import ParamPresetSelector from "@/components/ParamPresetSelector.vue";
import CssPresetEditor from "@/components/CssPresetEditor.vue";
import AlertDialog from "@/components/AlertDialog.vue";
import ExtensionManager from "@/components/ExtensionManager.vue";
import ExtensionSlot from "@/extensions/ExtensionSlot.vue";
import { Sidebar, Palette, SlidersHorizontal, Plug, Blocks } from "lucide-vue-next";
import { useChatStore } from "@/stores/chat";
import { useParamPresetsStore } from "@/stores/paramPresets";
import { useCssPresetsStore } from "@/stores/cssPresets";
import { useExtensionsStore } from "@/stores/extensions";
```

具体改动：删除 `import CssPresetSelector from "@/components/CssPresetSelector.vue";`，新增 `import { Sidebar, Palette, SlidersHorizontal, Plug, Blocks } from "lucide-vue-next";`

- [ ] **Step 2: 修改模板 — 替换 5 个按钮**

将 template 区域（第 3-14 行）中：

```vue
<header class="top-bar">
  <div class="top-left">
    <button class="top-btn" @click="showConversations = !showConversations">会话记录</button>
    <span class="top-title">Chat</span>
  </div>
  <nav class="top-nav">
    <CssPresetSelector @open-drawer="toggleDrawer('css')" />
    <button class="top-btn" @click="toggleDrawer('presets')">预设</button>
    <button class="top-btn" @click="toggleDrawer('api')">API 设置</button>
    <button class="top-btn" @click="toggleDrawer('extensions')">扩展</button>
  </nav>
</header>
```

替换为：

```vue
<header class="top-bar">
  <div class="top-left">
    <button class="top-btn" :class="{ active: showConversations }"
      @click="showConversations = !showConversations" title="会话记录">
      <Sidebar :size="18" />
    </button>
    <span class="top-title">Chat</span>
  </div>
  <nav class="top-nav">
    <button class="top-btn" :class="{ active: activeDrawer === 'css' }"
      @click="toggleDrawer('css')" title="CSS 预设">
      <Palette :size="18" />
    </button>
    <button class="top-btn" :class="{ active: activeDrawer === 'presets' }"
      @click="toggleDrawer('presets')" title="参数预设">
      <SlidersHorizontal :size="18" />
    </button>
    <button class="top-btn" :class="{ active: activeDrawer === 'api' }"
      @click="toggleDrawer('api')" title="API 设置">
      <Plug :size="18" />
    </button>
    <button class="top-btn" :class="{ active: activeDrawer === 'extensions' }"
      @click="toggleDrawer('extensions')" title="扩展管理">
      <Blocks :size="18" />
    </button>
  </nav>
</header>
```

- [ ] **Step 3: 验证 Vite 构建不报错**

```bash
cd frontend
npx vite build --mode development 2>&1 | tail -5
```

Expected: 无 import 错误，构建成功。

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.vue
git commit -m "feat: replace toolbar text buttons with Lucide SVG icons"
```

---

### Task 3: 更新 App.vue — 样式

**Files:**
- Modify: `frontend/src/App.vue`（`<style>` 块中的 `.top-btn` 样式）

**Interfaces:**
- Consumes: 已替换为图标的模板（Task 2）
- Produces: 36×36 正方按钮 + `.top-btn.active` 激活态下划线常驻

- [ ] **Step 1: 修改 `.top-btn` 样式**

将现有的 `.top-btn` 样式（第 161-190 行）：

```css
.top-btn {
  padding: 6px 14px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  position: relative;
  transition: all 0.15s ease;
}
.top-btn::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 2px;
  background: var(--accent);
  border-radius: 2px;
  transition: width 0.15s ease;
}
.top-btn:hover {
  color: var(--text-primary);
  transform: translateY(-1px);
}
.top-btn:hover::after {
  width: 60%;
}
```

替换为：

```css
.top-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  position: relative;
  transition: all 0.15s ease;
}
.top-btn::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 2px;
  background: var(--accent);
  border-radius: 2px;
  transition: width 0.15s ease;
}
.top-btn:hover {
  color: var(--text-primary);
  transform: translateY(-1px);
}
.top-btn:hover::after {
  width: 60%;
}
/* 激活态 */
.top-btn.active {
  color: var(--text-primary);
}
.top-btn.active::after {
  width: 100%;
}
```

关键变更：移除 `padding` 和 `font-size`，新增 `width: 36px; height: 36px; display: flex; align-items: center; justify-content: center;`，新增 `&.active` 规则块。

- [ ] **Step 2: 验证样式正确**

```bash
cd frontend
npx vite build --mode development 2>&1 | tail -3
```

Expected: 构建成功，无 CSS 相关错误。

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.vue
git commit -m "style: update .top-btn to 36x36 icon button with active underline"
```

---

### Task 4: 清理 CssPresetSelector 引用

**Files:**
- Delete: `frontend/src/components/CssPresetSelector.vue`
- Verify: `frontend/src/` 下无其他文件引用 CssPresetSelector

- [ ] **Step 1: 确认无残留引用**

```bash
cd frontend
grep -r "CssPresetSelector" src/ --include="*.vue" --include="*.js"
```

Expected: 无输出（Task 2 已在 App.vue 中移除 import 和模板引用）。

- [ ] **Step 2: 删除 CssPresetSelector.vue**

```bash
rm frontend/src/components/CssPresetSelector.vue
```

- [ ] **Step 3: 再次构建验证**

```bash
cd frontend
npx vite build --mode development 2>&1 | tail -3
```

Expected: 构建成功（确认删除后无导入错误）。

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/CssPresetSelector.vue
git commit -m "refactor: remove CssPresetSelector, replaced by inline icon button"
```

---

### Task 5: 端到端验证

**Files:**
- 无新文件创建或修改

- [ ] **Step 1: 启动开发服务器**

```bash
cd frontend
npx vite --host 127.0.0.1 &
sleep 3
```

- [ ] **Step 2: 手动验证清单**

在浏览器打开 `http://127.0.0.1:5173`，逐项检查：

| 检查项 | 预期 |
|--------|------|
| 5 个图标按钮可见（sidebar / palette / sliders-horizontal / plug / blocks） | ✅ |
| 默认颜色为灰（`#5b5b7a`） | ✅ |
| hover 时图标变深（`#1a1a2e`）+ 底部蓝色下划线展开 | ✅ |
| 点击"会话记录"，左侧抽屉打开，按钮下划线常驻 | ✅ |
| 点击"API 设置"，右侧抽屉打开，按钮下划线常驻 | ✅ |
| 同时打开左右抽屉，两按钮均显示下划线 | ✅ |
| 再次点击同一按钮，抽屉关闭，下划线消失 | ✅ |
| 缩小窗口，5 个图标按钮不溢出不换行 | ✅ |
| 原生 title tooltip 在 hover 时显示正确文字 | ✅ |

- [ ] **Step 3: 停止开发服务器**

```bash
kill %1 2>/dev/null
```

- [ ] **Step 4: Commit（如有修正）**

```bash
git status
# 如有任何修正
git add frontend/src/App.vue
git commit -m "fix: toolbar icon adjustments after manual testing"
```

---

### Task 6: 最终构建验证

**Files:**
- 无

- [ ] **Step 1: 生产构建**

```bash
cd frontend
npm run electron:build -- --dir 2>&1 | tail -10
```

Expected: Electron 打包成功，无图标渲染异常。

- [ ] **Step 2: Commit 最终状态**

```bash
git status
# 确认干净
```
