<template>
  <div class="preset-area">
    <!-- 正常模式：下拉 + 按钮 -->
    <div v-if="mode === 'normal'" class="preset-row">
      <select v-model="store.activePresetId" class="preset-select" @change="onSelect">
        <option :value="null" disabled>请选择预设</option>
        <option v-for="p in store.presets" :key="p.id" :value="p.id">
          {{ p.name }}
        </option>
      </select>
      <button class="preset-btn" title="保存" @click="handleSave" :disabled="!store.activePresetId">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
      </button>
      <button class="preset-btn" title="新建" @click="startNew">+</button>
      <button
        class="preset-btn"
        :class="{ 'danger-confirm': deleteConfirm }"
        :title="deleteConfirm ? '再次点击确认删除' : '删除'"
        @click="handleDelete"
        :disabled="!store.activePresetId"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
      </button>
    </div>

    <!-- 新建模式：内联输入框 -->
    <div v-if="mode === 'new'" class="preset-row">
      <input
        ref="newNameInput"
        v-model="newName"
        class="preset-input"
        placeholder="输入预设名称，回车确认"
        @keydown.enter="confirmNew"
        @keydown.escape="cancelNew"
      />
      <button class="preset-btn preset-btn-ok" title="确认" @click="confirmNew" :disabled="!newName.trim()">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
      </button>
      <button class="preset-btn preset-btn-cancel" title="取消" @click="cancelNew">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
    </div>

    <!-- 状态提示 -->
    <transition name="fade">
      <span v-if="toastMsg" class="preset-toast">{{ toastMsg }}</span>
    </transition>
  </div>
</template>

<script setup>
import { ref, nextTick } from "vue";
import { useSettingsStore } from "@/stores/settings";
const store = useSettingsStore();

const mode = ref("normal");   // "normal" | "new"
const newName = ref("");
const newNameInput = ref(null);
const deleteConfirm = ref(false);
const toastMsg = ref("");
let toastTimer = null;

function onSelect() {
  store.selectPreset(store.activePresetId);
}

// ── 新建 ──────────────────────────────────────────
async function startNew() {
  // 清空当前表单字段，避免用旧预设的数据创建新预设
  store.activePresetId = null;
  store.apiUrl = "";
  store.apiKey = "";
  store.model = "gpt-4o";
  store.responseFormat = "";
  mode.value = "new";
  newName.value = "";
  await nextTick();
  newNameInput.value?.focus();
}

async function confirmNew() {
  const name = newName.value.trim();
  if (!name) return;
  try {
    await store.createPreset(name);
    mode.value = "normal";
    showToast("预设已创建");
  } catch (e) {
    showToast("创建失败: " + (e.message || "未知错误"));
  }
}

function cancelNew() {
  mode.value = "normal";
  newName.value = "";
}

// ── 保存 ──────────────────────────────────────────
async function handleSave() {
  try {
    await store.savePreset();
    showToast("保存成功");
  } catch (e) {
    showToast("保存失败: " + (e.message || "未知错误"));
  }
}

// ── 删除 ──────────────────────────────────────────
async function handleDelete() {
  if (!deleteConfirm.value) {
    deleteConfirm.value = true;
    setTimeout(() => { deleteConfirm.value = false; }, 3000);
    return;
  }
  deleteConfirm.value = false;
  try {
    await store.deletePreset(store.activePresetId);
    showToast("已删除");
  } catch (e) {
    showToast("删除失败: " + (e.message || "未知错误"));
  }
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

/* 新建模式的输入框 */
.preset-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #4a90d9;
  border-radius: 8px;
  font-size: 14px;
  color: #333;
  outline: none;
  font-family: inherit;
  background: #f8fbff;
}
.preset-input:focus {
  border-color: #357abd;
  box-shadow: 0 0 0 2px rgba(74, 144, 217, 0.15);
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

.preset-btn-ok {
  border-color: #4caf50;
  color: #4caf50;
}
.preset-btn-ok:hover:not(:disabled) {
  background: #e8f5e9;
  color: #388e3c;
}
.preset-btn-ok:disabled {
  opacity: 0.3;
}

.preset-btn-cancel {
  border-color: #ef5350;
  color: #ef5350;
}
.preset-btn-cancel:hover:not(:disabled) {
  background: #ffebee;
  color: #d32f2f;
}

/* 删除按钮"确认删除"状态——变红闪烁 */
.preset-btn.danger-confirm {
  background: #ffebee;
  border-color: #ef5350;
  color: #ef5350;
  animation: pulse-danger 0.8s infinite;
}
@keyframes pulse-danger {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239, 83, 80, 0.4); }
  50%      { box-shadow: 0 0 0 4px rgba(239, 83, 80, 0); }
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
</style>
