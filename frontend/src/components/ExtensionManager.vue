<template>
  <div class="ext-manager">
    <!-- 工具栏 -->
    <div class="ext-toolbar">
      <h3 class="ext-title">扩展管理</h3>
      <div class="ext-actions">
        <button class="ext-btn ext-btn-install" @click="showZipDialog = true">📦 导入 ZIP</button>
        <button class="ext-btn ext-btn-install" @click="showGitDialog = true">🔗 Git 安装</button>
      </div>
    </div>

    <!-- 扩展列表 -->
    <div v-if="store.loading" class="ext-loading">加载中…</div>
    <div v-else-if="store.items.length === 0" class="ext-empty">暂无已安装的扩展</div>
    <div v-else class="ext-list">
      <div
        v-for="ext in store.items"
        :key="ext.id"
        class="ext-card"
        :class="{ 'ext-disabled': !ext.enabled }"
      >
        <div class="ext-info">
          <div class="ext-name">
            {{ ext.name || ext.id }}
            <span class="ext-version">v{{ ext.version || '0.0.0' }}</span>
          </div>
          <div class="ext-desc">{{ ext.description || '无描述' }}</div>
          <div class="ext-id">ID: {{ ext.id }}</div>
        </div>
        <div class="ext-controls">
          <label class="ext-toggle" title="启用/禁用">
            <input
              type="checkbox"
              :checked="ext.enabled"
              @change="onToggle(ext)"
            />
            <span class="toggle-label">{{ ext.enabled ? '已启用' : '已禁用' }}</span>
          </label>
          <button class="ext-btn ext-btn-update" @click="onUpdate(ext)">更新</button>
          <button class="ext-btn ext-btn-uninstall" @click="confirmUninstall(ext)">卸载</button>
        </div>
      </div>
    </div>

    <!-- ZIP 导入弹窗 -->
    <BaseDialog :visible="showZipDialog" title="导入 ZIP 扩展" @close="showZipDialog = false">
      <div class="dialog-body-inner">
        <input
          ref="zipInput"
          type="file"
          accept=".zip"
          class="dialog-input"
          @change="onZipSelected"
        />
        <div v-if="zipError" class="ext-error">{{ zipError }}</div>
      </div>
      <template #footer>
        <button class="dialog-btn dialog-btn-cancel" @click="showZipDialog = false">取消</button>
      </template>
    </BaseDialog>

    <!-- Git 安装弹窗 -->
    <BaseDialog :visible="showGitDialog" title="从 Git 安装扩展" @close="showGitDialog = false">
      <div class="dialog-body-inner">
        <input
          v-model="gitUrl"
          type="text"
          class="dialog-input"
          placeholder="Git 仓库地址（https://...）"
        />
        <input
          v-model="gitBranch"
          type="text"
          class="dialog-input"
          placeholder="分支（默认 main）"
        />
        <div v-if="gitError" class="ext-error">{{ gitError }}</div>
      </div>
      <template #footer>
        <button class="dialog-btn dialog-btn-cancel" @click="showGitDialog = false">取消</button>
        <button class="dialog-btn dialog-btn-ok" :disabled="!gitUrl.trim()" @click="onGitInstall">安装</button>
      </template>
    </BaseDialog>

    <!-- 权限审批弹窗 -->
    <BaseDialog
      :visible="!!store.pendingApproval"
      title="扩展权限审批"
      @close="store.cancelInstall()"
    >
      <div v-if="store.pendingApproval" class="dialog-body-inner">
        <p class="approval-intro">
          扩展 <strong>{{ store.pendingApproval.name || store.pendingApproval.id }}</strong> 请求以下权限：
        </p>
        <ul v-if="store.pendingApproval.permissions?.length" class="perm-list">
          <li v-for="p in store.pendingApproval.permissions" :key="p" class="perm-item">{{ p }}</li>
        </ul>
        <p v-else class="perm-none">无特殊权限要求</p>
      </div>
      <template #footer>
        <button class="dialog-btn dialog-btn-cancel" @click="store.cancelInstall()">拒绝</button>
        <button class="dialog-btn dialog-btn-ok" @click="onApprove">批准安装</button>
      </template>
    </BaseDialog>

    <!-- 卸载确认弹窗 -->
    <BaseDialog
      :visible="!!uninstallTarget"
      title="确认卸载"
      @close="uninstallTarget = null"
    >
      <div class="dialog-body-inner dialog-danger">
        <p class="dialog-danger-msg">
          确定要卸载扩展 <strong>{{ uninstallTarget?.name || uninstallTarget?.id }}</strong> 吗？此操作不可撤销。
        </p>
      </div>
      <template #footer>
        <button class="dialog-btn dialog-btn-cancel" @click="uninstallTarget = null">取消</button>
        <button class="dialog-btn dialog-btn-danger" @click="onUninstall">确认卸载</button>
      </template>
    </BaseDialog>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useExtensionsStore } from '@/stores/extensions';
import BaseDialog from '@/components/BaseDialog.vue';

const store = useExtensionsStore();

// ZIP 安装
const showZipDialog = ref(false);
const zipInput = ref(null);
const zipError = ref('');

function onZipSelected(e) {
  zipError.value = '';
  const file = e.target.files?.[0];
  if (!file) return;
  store.installZip(file).then(() => {
    showZipDialog.value = false;
    // 重置 input，否则再次选择同一文件不触发 change
    if (zipInput.value) zipInput.value.value = '';
  }).catch(err => {
    zipError.value = err?.message || '安装失败';
  });
}

// Git 安装
const showGitDialog = ref(false);
const gitUrl = ref('');
const gitBranch = ref('main');
const gitError = ref('');

function onGitInstall() {
  gitError.value = '';
  if (!gitUrl.value.trim()) return;
  store.installGit(gitUrl.value.trim(), gitBranch.value.trim() || 'main').then(() => {
    showGitDialog.value = false;
    gitUrl.value = '';
    gitBranch.value = 'main';
  }).catch(err => {
    gitError.value = err?.message || '安装失败';
  });
}

// 权限审批
function onApprove() {
  const pending = store.pendingApproval;
  store.confirmInstall(pending?.permissions || []);
}

// 卸载
const uninstallTarget = ref(null);
function confirmUninstall(ext) {
  uninstallTarget.value = ext;
}
function onUninstall() {
  if (!uninstallTarget.value) return;
  store.uninstall(uninstallTarget.value.id).then(() => {
    uninstallTarget.value = null;
  });
}

// 开关
function onToggle(ext) {
  store.toggle(ext.id, !ext.enabled);
}

// 更新
function onUpdate(ext) {
  store.update(ext.id);
}
</script>

<style scoped>
.ext-manager {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 工具栏 */
.ext-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.ext-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.ext-actions {
  display: flex;
  gap: 8px;
}

/* 按钮 */
.ext-btn {
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid transparent;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
  font-family: inherit;
  white-space: nowrap;
}

.ext-btn-install {
  background: #4a90d9;
  color: #fff;
}
.ext-btn-install:hover {
  background: #357abd;
}

.ext-btn-update {
  background: #f0f7ff;
  color: #4a90d9;
  border-color: #b8d4f0;
}
.ext-btn-update:hover {
  background: #dceeff;
}

.ext-btn-uninstall {
  background: #fff;
  color: #ef5350;
  border-color: #f5c6cb;
}
.ext-btn-uninstall:hover {
  background: #fff5f5;
}

/* 扩展列表 */
.ext-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ext-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border: 1px solid #e5e5e5;
  border-radius: 10px;
  background: #fff;
  transition: opacity 0.2s;
}

.ext-card.ext-disabled {
  opacity: 0.55;
}

.ext-info {
  flex: 1;
  min-width: 0;
}

.ext-name {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
}

.ext-version {
  font-size: 12px;
  font-weight: 400;
  color: #999;
  background: #f5f5f5;
  padding: 1px 6px;
  border-radius: 4px;
}

.ext-desc {
  font-size: 13px;
  color: #888;
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ext-id {
  font-size: 11px;
  color: #bbb;
  margin-top: 2px;
  font-family: monospace;
}

.ext-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

/* 开关 */
.ext-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  user-select: none;
}

.ext-toggle input {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #4a90d9;
}

.toggle-label {
  font-size: 12px;
  color: #888;
}

/* 错误 */
.ext-error {
  font-size: 13px;
  color: #ef5350;
  margin-top: 4px;
}

/* 加载 / 空 */
.ext-loading,
.ext-empty {
  font-size: 14px;
  color: #999;
  text-align: center;
  padding: 32px 0;
}

/* 权限列表 */
.approval-intro {
  font-size: 14px;
  color: #555;
  margin: 0 0 8px;
  line-height: 1.6;
}

.perm-list {
  margin: 0;
  padding: 0 0 0 20px;
  list-style: disc;
}

.perm-item {
  font-size: 13px;
  color: #666;
  padding: 2px 0;
  font-family: monospace;
}

.perm-none {
  font-size: 13px;
  color: #999;
  margin: 0;
}

/* 弹窗内部 */
.dialog-body-inner {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
</style>
