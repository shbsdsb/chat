<template>
  <div class="preset-area">
    <div class="preset-row">
      <select v-model="store.activePresetId" class="preset-select" @change="onSelect">
        <option :value="null" disabled>请选择预设</option>
        <option v-for="p in store.presets" :key="p.id" :value="p.id">
          {{ p.name }}
        </option>
      </select>
      <button class="preset-btn" title="保存" @click="handleSave" :disabled="!canSave">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
      </button>
      <button class="preset-btn" title="新建" @click="clearForm">+</button>
      <button
        class="preset-btn"
        title="删除"
        @click="handleDelete"
        :disabled="!store.activePresetId"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
      </button>
    </div>

    <!-- 状态提示 -->
    <transition name="fade">
      <span v-if="toastMsg" class="preset-toast">{{ toastMsg }}</span>
    </transition>

    <!-- 删除确认弹窗 -->
    <BaseDialog :visible="showDeleteDialog" title=" " @close="cancelDelete">
      <div class="dialog-danger">
        <div class="dialog-danger-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#ef5350" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        </div>
        <p class="dialog-danger-msg">确定要删除预设「{{ deletingPresetName }}」吗？此操作不可撤销。</p>
      </div>
      <template #footer>
        <button class="dialog-btn dialog-btn-cancel" @click="cancelDelete">取消</button>
        <button class="dialog-btn dialog-btn-danger" @click="confirmDelete">确定删除</button>
      </template>
    </BaseDialog>

    <!-- 命名弹窗：保存新预设 -->
    <BaseDialog :visible="showNameDialog" title="保存预设" @close="cancelNameDialog">
      <input
        ref="nameInput"
        v-model="dialogName"
        class="dialog-input"
        @keydown.enter="confirmNameDialog"
        @keydown.escape="cancelNameDialog"
      />
      <template #footer>
        <button class="dialog-btn dialog-btn-cancel" @click="cancelNameDialog">取消</button>
        <button class="dialog-btn dialog-btn-ok" @click="confirmNameDialog" :disabled="!dialogName.trim()">确认</button>
      </template>
    </BaseDialog>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from "vue";
import { useSettingsStore } from "@/stores/settings";
import { useAlertStore } from "@/stores/alert";
import BaseDialog from "@/components/BaseDialog.vue";
const store = useSettingsStore();
const alert = useAlertStore();

const showDeleteDialog = ref(false);
const deletingPresetName = ref("");
const toastMsg = ref("");
let toastTimer = null;

// ── 保存按钮可用性 ──────────────────────────────
const canSave = computed(() => {
  return !!(store.apiUrl?.trim() && store.apiKey?.trim() && store.model?.trim());
});

// ── 命名弹窗 ────────────────────────────────────
const showNameDialog = ref(false);
const dialogName = ref("");
const nameInput = ref(null);

function onSelect() {
  store.selectPreset(store.activePresetId);
}

// ── 新建（仅清空表单，保存由保存按钮负责）──────────
function clearForm() {
  store.activePresetId = null;
  store.apiUrl = "";
  store.apiKey = "";
  store.model = "gpt-4o";
  store.responseFormat = "";
}

// ── 保存 ──────────────────────────────────────────
async function handleSave() {
  if (!canSave.value) {
    alert.warning("表单不完整", "请填写完整的 API URL、API Key 和 Model");
    return;
  }

  // 编辑已有预设 → 直接更新
  if (store.activePresetId) {
    try {
      await store.savePreset();
      showToast("保存成功");
    } catch (e) {
      alert.error("保存失败", e.message || "未知错误");
    }
    return;
  }

  // 新建预设：生成预命名（model 名，重复则追加 (1)(2)...）
  let base = store.model.trim();
  let candidate = base;
  let n = 1;
  while (store.presets.some((p) => p.name === candidate)) {
    candidate = `${base}(${n})`;
    n++;
  }
  dialogName.value = candidate;
  showNameDialog.value = true;
  await nextTick();
  nameInput.value?.focus();
  nameInput.value?.select();
}

// ── 命名弹窗操作 ────────────────────────────────
async function confirmNameDialog() {
  const name = dialogName.value.trim();
  if (!name) return;
  showNameDialog.value = false;
  try {
    await store.createPreset(name);
    showToast("预设已保存");
  } catch (e) {
    alert.error("保存失败", e.message || "未知错误");
  }
}

function cancelNameDialog() {
  showNameDialog.value = false;
  dialogName.value = "";
}

// ── 删除 ──────────────────────────────────────────
function handleDelete() {
  const preset = store.presets.find((p) => p.id === store.activePresetId);
  deletingPresetName.value = preset?.name || "未命名";
  showDeleteDialog.value = true;
}

async function confirmDelete() {
  showDeleteDialog.value = false;
  try {
    await store.deletePreset(store.activePresetId);
    showToast("已删除");
  } catch (e) {
    alert.error("删除失败", e.message || "未知错误");
  }
}

function cancelDelete() {
  showDeleteDialog.value = false;
}

// ── Toast ─────────────────────────────────────────
function showToast(msg) {
  toastMsg.value = msg;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toastMsg.value = ""; }, 2000);
}
</script>

<style scoped>
.preset-area {
  position: relative;
}

.preset-row {
  display: flex;
  gap: 6px;
  align-items: center;
}

.preset-select {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d5d5d5;
  border-radius: 8px;
  font-size: 14px;
  color: #333;
  background: #fff;
  outline: none;
  font-family: inherit;
}

.preset-btn {
  width: 32px;
  height: 32px;
  border: 1px solid #d5d5d5;
  border-radius: 6px;
  background: #fff;
  color: #666;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  line-height: 1;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.preset-btn:hover:not(:disabled) {
  background: #f0f0f0;
  color: #333;
}
.preset-btn:disabled {
  opacity: 0.3;
  cursor: default;
}

/* Toast 提示 */
.preset-toast {
  position: absolute;
  top: -28px;
  left: 0;
  font-size: 12px;
  color: #555;
  background: #f5f5f5;
  padding: 3px 10px;
  border-radius: 4px;
  white-space: nowrap;
  pointer-events: none;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ── 弹窗通用 ─────────────────────────────────── */
</style>
