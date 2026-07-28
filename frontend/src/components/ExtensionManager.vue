<template>
  <div class="ext-manager-root">
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

    <!-- 加载/空态 -->
    <div v-if="store.loading" class="empty">加载中…</div>
    <div v-else-if="store.items.length === 0" class="empty">暂无已安装的扩展</div>

    <!-- 扩展列表 -->
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
      <div class="modal-title">
        安装扩展
        <button class="modal-close" @click="showInstallModal = false">✕</button>
      </div>
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
          <input class="input-field input-mono" placeholder="选择 .zip 文件..." readonly :value="zipPath" style="flex:1;cursor:default;" />
          <label class="btn-sm outline" style="cursor:pointer;flex-shrink:0;">
            <FileText :size="14" /> 浏览
            <input ref="zipInput" type="file" accept=".zip" hidden @change="onZipPicked" />
          </label>
        </div>
      </div>
      <div v-if="installError" class="modal-error">{{ installError }}</div>
      <button class="btn-sm primary modal-install-btn" @click="onInstall">安装</button>
    </div>
  </div>

  <!-- 管理 Modal -->
  <div v-if="showManageModal" class="modal-overlay" @click.self="showManageModal = false">
    <div class="modal-box">
      <div class="modal-title">
        管理扩展
        <button class="modal-close" @click="showManageModal = false">✕</button>
      </div>
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

  <!-- 权限审批弹窗 -->
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
  </div>
</template>

<script setup>
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
const zipInput = ref(null);
const installError = ref('');

let _zipFile = null;

function onZipPicked(e) {
  const file = e.target.files?.[0];
  _zipFile = file;
  zipPath.value = file ? file.name : '';
}

async function onInstall() {
  installError.value = '';
  if (gitUrl.value.trim()) {
    try {
      await store.installGit(gitUrl.value.trim(), gitBranch.value.trim() || 'main');
      showInstallModal.value = false;
      gitUrl.value = '';
      gitBranch.value = 'main';
    } catch (e) { installError.value = e?.message || '安装失败'; }
    return;
  }
  if (!_zipFile) { installError.value = '请选择 ZIP 文件或输入 Git 地址'; return; }
  try {
    await store.installZip(_zipFile);
    showInstallModal.value = false;
    zipPath.value = '';
    _zipFile = null;
    if (zipInput.value) zipInput.value.value = '';
  } catch (e) { installError.value = e?.message || '安装失败'; }
}

// 卸载
const uninstallTarget = ref(null);
function confirmUninstall(ext) { uninstallTarget.value = ext; }
async function onUninstall() {
  if (!uninstallTarget.value) return;
  try { await store.uninstall(uninstallTarget.value.id); uninstallTarget.value = null; }
  catch (e) { /* store handles alert */ }
}

// 开关 & 更新
function onToggle(ext) { store.toggle(ext.id, !ext.enabled); }
function onUpdate(ext) { store.update(ext.id); }
</script>

<style scoped>
.ext-manager-root { display: contents; }

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

/* 更新按钮绿点 */
.update-dot { position: relative; }
.update-dot::after { content: ""; position: absolute; top: -3px; right: -3px; width: 7px; height: 7px; background: #22c55e; border-radius: 50%; border: 1.5px solid var(--bg-primary); }

/* ——— 扩展项 ——— */
.ext-item { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 14px; border: 1px solid var(--border-light); border-radius: var(--radius-md); background: var(--bg-input); margin-bottom: 8px; transition: opacity 0.2s; }
.ext-item:last-child { margin-bottom: 0; }
.ext-item.disabled { opacity: 0.45; }
.ext-info { flex: 1; min-width: 0; }
.ext-name-row { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
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
</style>
