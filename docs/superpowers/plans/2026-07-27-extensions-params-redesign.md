# 扩展管理 & 参数预设 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 ExtensionManager 和 ParamPresetSelector 改为卡片式布局，统一使用 CSS 变量和 Lucide 图标。

**Architecture:** 两个组件重写模板和样式，不改变 Pinia store 和 API 层。ExtensionManager 新增安装 Modal 和管理 Modal，管理 Modal 中更新按钮条件显示。

**Tech Stack:** Vue 3 (Composition API), Pinia, CSS Variables, Lucide Vue Next

## Global Constraints

- 全部颜色使用 `var(--xxx)`，零硬编码（tokens.css 为唯一来源）
- 表单控件统一：`bg: var(--bg-input)`, `border: 1px solid var(--border-light)`, `radius: var(--radius-sm)=8px`
- focus 态统一：`border-color: var(--accent)` + `box-shadow: var(--focus-ring)`
- disabled 统一 `opacity: 0.45`
- 卡片边框 `var(--border)`, 圆角 `var(--radius-lg)=16px`, 阴影 `var(--shadow-sm)`
- toggle-box 与 API 设置一致：`18×18`, `border-radius: 4px`, accent 底 + 白色 ✓
- 不在此范围：ExtensionDetailDrawer、BaseDialog、后端 API、CSS 预设系统

---

### Task 1: 重写 ParamPresetSelector.vue — 卡片式 + Lucide 图标

**Files:**
- Modify: `frontend/src/components/ParamPresetSelector.vue`

- [ ] **Step 1: 重写模板**

```vue
<template>
  <div class="card">
    <div class="card-header">
      <span class="card-icon"><SlidersHorizontal :size="18" /></span>
      <span class="card-label">参数预设</span>
    </div>

    <!-- 预设选择行 -->
    <div class="pp-row">
      <select v-model="store.activePresetId" class="input-field" style="flex:1;min-width:140px;" @change="onSelect">
        <option :value="null" disabled>请选择预设</option>
        <option v-for="p in store.presets" :key="p.id" :value="p.id">{{ p.name }}</option>
      </select>
      <button class="icon-btn" title="新建" @click="clearForm">+</button>
      <button class="icon-btn danger" title="删除" @click="handleDelete" :disabled="!store.activePresetId">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
      </button>
    </div>

    <!-- 参数表单 -->
    <div style="display:flex;flex-direction:column;gap:10px;margin-bottom:14px;">
      <div>
        <span class="field-label">Temperature</span>
        <input v-model.number="form.temperature" type="number" class="input-field" step="0.1" min="0" max="2" style="cursor:text;" />
      </div>
      <div>
        <span class="field-label">Max Tokens</span>
        <input v-model.number="form.maxTokens" type="number" class="input-field" step="1" min="1" style="cursor:text;" />
      </div>
      <div>
        <span class="field-label">Top P</span>
        <input v-model.number="form.topP" type="number" class="input-field" step="0.01" min="0" max="1" style="cursor:text;" />
      </div>
    </div>

    <!-- 保存按钮 -->
    <button class="btn-save" @click="handleSave" :disabled="!store.activePresetId">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
      保存
    </button>

    <!-- Toast -->
    <transition name="fade"><span v-if="toastMsg" class="pp-toast">{{ toastMsg }}</span></transition>

    <!-- 删除确认弹窗（沿用原 BaseDialog） -->
    <BaseDialog :visible="showDeleteDialog" title=" " @close="cancelDelete">
      <div class="dialog-danger">
        <p class="dialog-danger-msg">确定要删除预设「{{ deletingPresetName }}」吗？此操作不可撤销。</p>
      </div>
      <template #footer>
        <button class="dialog-btn dialog-btn-cancel" @click="cancelDelete">取消</button>
        <button class="dialog-btn dialog-btn-danger" @click="confirmDelete">确定删除</button>
      </template>
    </BaseDialog>

    <!-- 命名弹窗 -->
    <BaseDialog :visible="showNameDialog" title="新建预设" @close="cancelNameDialog">
      <input ref="nameInput" v-model="dialogName" class="dialog-input" placeholder="输入预设名称" @keydown.enter="confirmNameDialog" />
      <template #footer>
        <button class="dialog-btn dialog-btn-cancel" @click="cancelNameDialog">取消</button>
        <button class="dialog-btn dialog-btn-ok" @click="confirmNameDialog" :disabled="!dialogName.trim()">确认</button>
      </template>
    </BaseDialog>
  </div>
</template>
```

- [ ] **Step 2: 重写 script（添加 Lucide import）**

在现有 imports 顶部添加：
```js
import { SlidersHorizontal } from "lucide-vue-next";
```

其余逻辑不变（form reactive、watch、handleSave、名称弹窗逻辑等全部保留）。

- [ ] **Step 3: 重写样式（非 scoped）**

```css
/* 卡片 */
.card {
  background: var(--bg-primary); border: 1px solid var(--border);
  border-radius: var(--radius-lg); box-shadow: var(--shadow-sm);
  padding: 16px 18px; display: flex; flex-direction: column;
}
.card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; }
.card-icon { color: var(--accent); display: flex; align-items: center; width: 20px; height: 20px; }
.card-label { font-size: 13px; font-weight: 600; color: var(--text-secondary); }

/* 预设选择行 */
.pp-row { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; margin-bottom: 14px; }

/* 表单 */
.input-field {
  width: 100%; padding: 7px 10px;
  border: 1px solid var(--border-light); border-radius: var(--radius-sm);
  font-size: 13px; color: var(--text-primary);
  background: var(--bg-input); outline: none;
  font-family: inherit; transition: border-color 0.15s, box-shadow 0.15s;
}
.input-field:focus { border-color: var(--accent); box-shadow: var(--focus-ring); }
.field-label {
  font-size: 11px; font-weight: 500; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: 0.3px; margin-bottom: 4px; display: block;
}

/* 图标按钮 */
.icon-btn {
  width: 32px; height: 32px; border: 1px solid var(--border-light);
  border-radius: var(--radius-sm); background: var(--bg-input); color: var(--text-secondary);
  cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  transition: all 0.15s; font-size: 16px; line-height: 1;
}
.icon-btn:hover { color: var(--text-primary); border-color: var(--border); background: var(--bg-input-hover); }
.icon-btn.danger:hover { color: var(--danger); border-color: var(--danger); background: var(--danger-bg); }
.icon-btn:disabled { opacity: 0.45; cursor: default; }

/* 保存按钮 */
.btn-save {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 18px; border: none; border-radius: var(--radius-sm);
  background: var(--accent); color: #fff; font-size: 13px; font-weight: 600;
  cursor: pointer; font-family: inherit;
  box-shadow: 0 1px 3px rgba(79,110,246,0.2);
  transition: all 0.15s;
}
.btn-save:hover:not(:disabled) { background: var(--accent-light); transform: translateY(-1px); box-shadow: 0 2px 6px rgba(79,110,246,0.3); }
.btn-save:disabled { opacity: 0.45; cursor: default; transform: none; box-shadow: none; }

/* Toast */
.pp-toast {
  position: absolute; top: -6px; left: 0;
  font-size: 12px; color: var(--text-secondary);
  background: var(--bg-input); padding: 3px 10px;
  border-radius: var(--radius-sm); white-space: nowrap; pointer-events: none;
}
.fade-enter-active, .fade-leave-active { transition: opacity 0.25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
```

删除原有的 `<style scoped>` 块，改用非 scoped。

- [ ] **Step 4: 验证构建**

```bash
cd frontend
npx vite build --mode development 2>&1 | tail -3
```
Expected: `✓ built in ...`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ParamPresetSelector.vue
git commit -m "feat: redesign ParamPresetSelector with card layout and Lucide icons"
```

---

### Task 2: 重写 ExtensionManager.vue — 卡片式 + Modal

**Files:**
- Modify: `frontend/src/components/ExtensionManager.vue`

- [ ] **Step 1: 重写模板**

```vue
<template>
  <div class="card">
    <!-- Header -->
    <div class="card-header">
      <span class="card-icon"><Blocks :size="18" /></span>
      <span class="card-label">已安装</span>
      <div style="flex:1;"></div>
      <button class="btn-sm primary" @click="showInstallModal = true">
        <Plus :size="14" />
        安装扩展
      </button>
      <button class="btn-sm outline" style="margin-left:6px;" @click="showManageModal = true">
        <Settings :size="14" />
        管理扩展
      </button>
    </div>

    <!-- 空态 -->
    <div v-if="store.loading" class="empty">加载中…</div>
    <div v-else-if="store.items.length === 0" class="empty">暂无已安装的扩展</div>

    <!-- 扩展列表（默认只显示名称+详情） -->
    <div v-else>
      <div v-for="ext in store.items" :key="ext.id" class="ext-item" :class="{ disabled: !ext.enabled }">
        <div class="ext-info">
          <div class="ext-name-row">
            <span class="ext-name">{{ ext.name || ext.id }}</span>
            <span class="ext-version">v{{ ext.version || '0.0.0' }}</span>
            <span class="ext-source">{{ ext.source || 'ZIP' }}</span>
          </div>
          <div class="ext-desc">{{ ext.description || '无描述' }}</div>
          <div class="ext-id">ID: {{ ext.id }}</div>
        </div>
        <div class="ext-controls">
          <button class="btn-sm outline" @click="store.openDetail(ext)">详情</button>
        </div>
      </div>
    </div>
  </div>

  <!-- 安装 Modal -->
  <div v-if="showInstallModal" class="modal-overlay" @click.self="showInstallModal = false">
    <div class="modal-box">
      <div class="modal-title">安装扩展 <button class="modal-close" @click="showInstallModal = false">✕</button></div>
      <div class="form-row">
        <span class="field-label">Git 仓库地址</span>
        <input v-model="gitUrl" class="input-field input-mono" placeholder="https://github.com/user/plugin.git" @keydown.escape="showInstallModal = false" />
      </div>
      <div class="form-row">
        <span class="field-label">分支（可选）</span>
        <input v-model="gitBranch" class="input-field" placeholder="main" />
      </div>
      <div class="divider"></div>
      <div class="form-row">
        <span class="field-label">ZIP 文件路径</span>
        <div class="row-gap">
          <input class="input-field input-mono" placeholder="选择 .zip 文件..." readonly :value="zipPath" style="flex:1;" />
          <label class="btn-sm outline" style="cursor:pointer;flex-shrink:0;">
            <FileText :size="14" /> 浏览
            <input type="file" accept=".zip" hidden @change="onZipPicked" />
          </label>
        </div>
      </div>
      <div class="modal-error" v-if="installError">{{ installError }}</div>
      <button class="btn-sm primary modal-install-btn" @click="onInstall">安装</button>
    </div>
  </div>

  <!-- 管理 Modal -->
  <div v-if="showManageModal" class="modal-overlay" @click.self="showManageModal = false">
    <div class="modal-box">
      <div class="modal-title">管理扩展 <button class="modal-close" @click="showManageModal = false">✕</button></div>
      <div v-for="ext in store.items" :key="ext.id" class="ext-item" :class="{ disabled: !ext.enabled }" style="margin-bottom:8px;">
        <div class="ext-info">
          <div class="ext-name-row">
            <span class="ext-name">{{ ext.name || ext.id }}</span>
            <span class="ext-version">v{{ ext.version || '0.0.0' }}</span>
            <span class="ext-source">{{ ext.source || 'ZIP' }}</span>
          </div>
          <div class="ext-desc">{{ ext.description || '' }}</div>
        </div>
        <div class="ext-controls">
          <label class="custom-toggle" @click.stop="onToggle(ext)">
            <div class="toggle-box" :class="{ on: ext.enabled }">
              <svg v-if="ext.enabled" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
            </div>
            <span class="toggle-label">{{ ext.enabled ? '已启用' : '已禁用' }}</span>
          </label>
          <button v-if="ext.hasUpdate" class="btn-sm outline-blue update-dot" @click="onUpdate(ext)">更新</button>
          <button class="btn-sm outline-red" @click="confirmUninstall(ext)">卸载</button>
        </div>
      </div>
    </div>
  </div>

  <!-- 卸载确认弹窗 -->
  <BaseDialog :visible="!!uninstallTarget" title="确认卸载" @close="uninstallTarget = null">
    <p style="font-size:14px;color:var(--text-secondary);margin:0;">确定要卸载 <strong>{{ uninstallTarget?.name }}</strong>？此操作不可撤销。</p>
    <template #footer>
      <button class="dialog-btn dialog-btn-cancel" @click="uninstallTarget = null">取消</button>
      <button class="dialog-btn dialog-btn-danger" @click="onUninstall">确认卸载</button>
    </template>
  </BaseDialog>

  <!-- 权限审批弹窗（保留原有逻辑） -->
  <BaseDialog :visible="!!store.pendingApproval" title="扩展权限审批" @close="store.cancelInstall()">
    <div v-if="store.pendingApproval">
      <p style="font-size:14px;color:var(--text-secondary);margin:0 0 8px;">扩展 <strong>{{ store.pendingApproval.name || store.pendingApproval.id }}</strong> 请求以下权限：</p>
      <ul v-if="store.pendingApproval.permissions?.length" style="padding-left:20px;color:var(--text-secondary);font-size:13px;font-family:monospace;">
        <li v-for="p in store.pendingApproval.permissions" :key="p">{{ p }}</li>
      </ul>
      <p v-else style="font-size:13px;color:var(--text-muted);">无特殊权限要求</p>
    </div>
    <template #footer>
      <button class="dialog-btn dialog-btn-cancel" @click="store.cancelInstall()">拒绝</button>
      <button class="dialog-btn dialog-btn-ok" @click="store.confirmInstall(store.pendingApproval?.permissions || [])">批准安装</button>
    </template>
  </BaseDialog>

  <ExtensionDetailDrawer />
</template>
```

- [ ] **Step 2: 重写 script**

```js
import { ref } from 'vue';
import { Blocks, Plus, Settings, FileText } from 'lucide-vue-next';
import { useExtensionsStore } from '@/stores/extensions';
import BaseDialog from '@/components/BaseDialog.vue';
import ExtensionDetailDrawer from '@/components/ExtensionDetailDrawer.vue';

const store = useExtensionsStore();

// Modals
const showInstallModal = ref(false);
const showManageModal = ref(false);

// Git install
const gitUrl = ref('');
const gitBranch = ref('main');
const zipPath = ref('');
const installError = ref('');

function onZipPicked(e) {
  const file = e.target.files?.[0];
  zipPath.value = file ? file.name : '';
  // 存储 file 对象供安装使用
  e.target._file = file;
}

async function onInstall() {
  installError.value = '';
  // Git 优先
  if (gitUrl.value.trim()) {
    try {
      await store.installGit(gitUrl.value.trim(), gitBranch.value.trim() || 'main');
      showInstallModal.value = false;
      gitUrl.value = '';
      gitBranch.value = 'main';
    } catch (e) { installError.value = e?.message || '安装失败'; }
    return;
  }
  // ZIP
  const fileInput = document.querySelector('input[type="file"]');
  const file = fileInput?._file;
  if (!file) { installError.value = '请选择 ZIP 文件或输入 Git 地址'; return; }
  try {
    await store.installZip(file);
    showInstallModal.value = false;
    zipPath.value = '';
  } catch (e) { installError.value = e?.message || '安装失败'; }
}

// 卸载
const uninstallTarget = ref(null);
function confirmUninstall(ext) { uninstallTarget.value = ext; }
async function onUninstall() {
  if (!uninstallTarget.value) return;
  try { await store.uninstall(uninstallTarget.value.id); uninstallTarget.value = null; }
  catch (e) { /* handled by store */ }
}

// 开关 & 更新
function onToggle(ext) { store.toggle(ext.id, !ext.enabled); }
function onUpdate(ext) { store.update(ext.id); }
```

- [ ] **Step 3: 重写样式**

```css
/* ——— 卡片 ——— */
.card { background: var(--bg-primary); border: 1px solid var(--border); border-radius: var(--radius-lg); box-shadow: var(--shadow-sm); padding: 16px 18px; display: flex; flex-direction: column; }
.card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.card-icon { color: var(--accent); display: flex; align-items: center; width: 20px; height: 20px; }
.card-label { font-size: 13px; font-weight: 600; color: var(--text-secondary); }

/* ——— 按钮 ——— */
.btn-sm { display: inline-flex; align-items: center; gap: 5px; padding: 7px 14px; border: none; border-radius: var(--radius-sm); font-size: 12px; font-weight: 600; cursor: pointer; font-family: inherit; white-space: nowrap; transition: all 0.15s; }
.btn-sm.primary { background: var(--accent); color: #fff; box-shadow: 0 1px 3px rgba(79,110,246,0.2); }
.btn-sm.primary:hover { background: var(--accent-light); transform: translateY(-1px); box-shadow: 0 2px 6px rgba(79,110,246,0.3); }
.btn-sm.outline { background: var(--bg-input); color: var(--text-secondary); border: 1px solid var(--border-light); }
.btn-sm.outline:hover { color: var(--text-primary); border-color: var(--border); background: var(--bg-input-hover); }
.btn-sm.outline-blue { background: var(--accent-bg); color: var(--accent); border: 1px solid rgba(79,110,246,0.2); }
.btn-sm.outline-blue:hover { background: rgba(79,110,246,0.14); }
.btn-sm.outline-red { background: var(--bg-input); color: var(--danger); border: 1px solid rgba(239,68,68,0.2); }
.btn-sm.outline-red:hover { background: var(--danger-bg); border-color: var(--danger); }
.btn-sm:disabled { opacity: 0.45; cursor: default; transform: none; box-shadow: none; }

/* 更新按钮绿点指示 */
.update-dot { position: relative; }
.update-dot::after { content: ""; position: absolute; top: -3px; right: -3px; width: 7px; height: 7px; background: #22c55e; border-radius: 50%; border: 1.5px solid var(--bg-primary); }

/* ——— 扩展项 ——— */
.ext-item { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 14px; border: 1px solid var(--border-light); border-radius: var(--radius-md); background: var(--bg-input); margin-bottom: 8px; transition: opacity 0.2s; }
.ext-item:last-child { margin-bottom: 0; }
.ext-item.disabled { opacity: 0.45; }
.ext-info { flex: 1; min-width: 0; }
.ext-name-row { display: flex; align-items: center; gap: 6px; }
.ext-name { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.ext-version { font-size: 11px; color: var(--text-muted); background: var(--bg-tertiary); padding: 1px 6px; border-radius: 4px; }
.ext-source { font-size: 10px; font-weight: 500; color: var(--text-muted); background: var(--bg-tertiary); padding: 1px 6px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.3px; }
.ext-desc { font-size: 12px; color: var(--text-muted); margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ext-id { font-size: 10px; color: var(--text-muted); font-family: monospace; margin-top: 1px; opacity: 0.7; }
.ext-controls { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }

/* ——— 空态 ——— */
.empty { font-size: 14px; color: var(--text-muted); text-align: center; padding: 32px 0; }

/* ——— Modal ——— */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.3); z-index: 100; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(2px); }
.modal-box { background: var(--bg-primary); border-radius: var(--radius-lg); box-shadow: var(--shadow-md); padding: 24px; width: 420px; max-width: 90vw; display: flex; flex-direction: column; gap: 14px; }
.modal-title { display: flex; align-items: center; justify-content: space-between; font-size: 15px; font-weight: 700; color: var(--text-primary); }
.modal-close { border: none; background: none; cursor: pointer; color: var(--text-muted); font-size: 18px; line-height: 1; }
.modal-install-btn { align-self: flex-end; padding: 8px 24px; font-size: 13px; }
.modal-error { font-size: 12px; color: var(--danger); }

/* ——— 表单 ——— */
.form-row { display: flex; flex-direction: column; gap: 4px; }
.field-label { font-size: 11px; font-weight: 500; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.3px; }
.input-field { width: 100%; padding: 7px 10px; border: 1px solid var(--border-light); border-radius: var(--radius-sm); font-size: 13px; color: var(--text-primary); background: var(--bg-input); outline: none; font-family: inherit; transition: border-color 0.15s, box-shadow 0.15s; }
.input-field:focus { border-color: var(--accent); box-shadow: var(--focus-ring); }
.input-mono { font-family: "Consolas", "Monaco", monospace; font-size: 12px; }
.row-gap { display: flex; gap: 6px; }
.divider { height: 1px; background: var(--border-light); }

/* ——— 自定义开关 ——— */
.custom-toggle { display: flex; align-items: center; gap: 6px; cursor: pointer; user-select: none; }
.toggle-box { width: 18px; height: 18px; border: 2px solid var(--border); border-radius: 4px; display: flex; align-items: center; justify-content: center; transition: all 0.15s; background: var(--bg-input); }
.toggle-box.on { background: var(--accent); border-color: var(--accent); }
.toggle-label { font-size: 12px; color: var(--text-muted); }
```

全部放入非 scoped `<style>` 块。删除原 `<style scoped>`。

- [ ] **Step 4: 验证构建**

```bash
cd frontend
npx vite build --mode development 2>&1 | tail -3
```
Expected: `✓ built in ...`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ExtensionManager.vue
git commit -m "feat: redesign ExtensionManager with card layout, install/manage modals, conditional update"
```

---

### Task 3: 端到端验证 + 文档

- [ ] **Step 1: 启动开发服务器**

```bash
cd frontend && npx vite --host 127.0.0.1 &
```

- [ ] **Step 2: 手动验证**

| # | 检查项 | 预期 |
|---|--------|------|
| 1 | 参数预设页面卡片式，SliderHorizontal 图标可见 | ✅ |
| 2 | 表单 input focus 蓝边框+发光环 | ✅ |
| 3 | 保存按钮 compact accent 色 | ✅ |
| 4 | 扩展管理页面卡片式，Blocks 图标可见 | ✅ |
| 5 | 点击"安装扩展"弹出 Modal，Git+ZIP 双区 | ✅ |
| 6 | 点击"管理扩展"弹出 Modal，开关+卸载可见 | ✅ |
| 7 | Git 扩展 hasUpdate=true 时显示"更新"按钮+绿点 | ✅ |
| 8 | ZIP 扩展无更新按钮 | ✅ |

- [ ] **Step 3: 停止服务器**

```bash
kill %1 2>/dev/null
```

- [ ] **Step 4: 生产构建**

```bash
cd frontend && npx vite build 2>&1 | tail -3
```
Expected: `✓ built in ...`

- [ ] **Step 5: 清理 + 提交文档**

```bash
rm -rf temp_extparampreview
git add docs/superpowers/specs/2026-07-27-extensions-params-redesign.md docs/superpowers/plans/2026-07-27-extensions-params-redesign.md
git commit -m "docs: add extensions & params redesign spec and implementation plan"
```
