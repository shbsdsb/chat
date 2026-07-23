<template>
  <div class="pp-area">
    <!-- 预设选择行 -->
    <div class="pp-row">
      <select v-model="store.activePresetId" class="pp-select" @change="onSelect">
        <option :value="null" disabled>请选择预设</option>
        <option v-for="p in store.presets" :key="p.id" :value="p.id">
          {{ p.name }}
        </option>
      </select>
      <button class="pp-btn" title="新建" @click="clearForm">+</button>
      <button
        class="pp-btn"
        title="删除"
        @click="handleDelete"
        :disabled="!store.activePresetId"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
      </button>
    </div>

    <!-- 参数表单 -->
    <div class="pp-fields">
      <label class="pp-label">
        Temperature
        <input
          v-model.number="form.temperature"
          type="number"
          class="pp-input"
          step="0.1"
          min="0"
          max="2"
        />
      </label>
      <label class="pp-label">
        Max Tokens
        <input
          v-model.number="form.maxTokens"
          type="number"
          class="pp-input"
          step="1"
          min="1"
        />
      </label>
      <label class="pp-label">
        Top P
        <input
          v-model.number="form.topP"
          type="number"
          class="pp-input"
          step="0.01"
          min="0"
          max="1"
        />
      </label>
    </div>

    <button class="pp-save-btn" @click="handleSave" :disabled="!store.activePresetId">保存</button>

    <!-- Toast -->
    <transition name="fade">
      <span v-if="toastMsg" class="pp-toast">{{ toastMsg }}</span>
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

    <!-- 命名弹窗 -->
    <BaseDialog :visible="showNameDialog" title="新建预设" @close="cancelNameDialog">
      <input
        ref="nameInput"
        v-model="dialogName"
        class="dialog-input"
        placeholder="输入预设名称"
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
import { ref, reactive, watch, nextTick } from "vue";
import { useParamPresetsStore } from "@/stores/paramPresets";
import { useAlertStore } from "@/stores/alert";
import BaseDialog from "@/components/BaseDialog.vue";

const store = useParamPresetsStore();
const alert = useAlertStore();

const emit = defineEmits(["saved"]);

const toastMsg = ref("");
let toastTimer = null;

const form = reactive({
  temperature: 0.7,
  maxTokens: 4096,
  topP: 1.0,
});

// 切换预设时同步表单
watch(() => store.activePresetId, (id) => {
  const p = store.presets.find((p) => p.id === id);
  if (p) {
    form.temperature = p.temperature;
    form.maxTokens = p.max_tokens;
    form.topP = p.top_p;
  }
});

function onSelect() {
  // activePresetId 已由 v-model 更新，watch 自动同步表单
}

// 新建
const showNameDialog = ref(false);
const dialogName = ref("");
const nameInput = ref(null);

function clearForm() {
  store.activePresetId = null;
  form.temperature = 0.7;
  form.maxTokens = 4096;
  form.topP = 1.0;

  let base = "新预设";
  let candidate = base;
  let n = 1;
  while (store.presets.some((p) => p.name === candidate)) {
    candidate = `${base} (${n})`;
    n++;
  }
  dialogName.value = candidate;
  showNameDialog.value = true;
  nextTick(() => {
    nameInput.value?.focus();
    nameInput.value?.select();
  });
}

async function confirmNameDialog() {
  const name = dialogName.value.trim();
  if (!name) return;
  showNameDialog.value = false;
  try {
    await store.createPreset(name, form.temperature, form.maxTokens, form.topP);
    showToast("预设已创建");
    emit("saved");
  } catch (e) {
    alert.error("创建失败", e.message || "未知错误");
  }
}

function cancelNameDialog() {
  showNameDialog.value = false;
  dialogName.value = "";
}

// 保存
async function handleSave() {
  if (!store.activePresetId) return;
  try {
    await store.savePreset(form.temperature, form.maxTokens, form.topP);
    showToast("保存成功");
  } catch (e) {
    alert.error("保存失败", e.message || "未知错误");
  }
}

// 删除
const showDeleteDialog = ref(false);
const deletingPresetName = ref("");

function handleDelete() {
  const p = store.presets.find((p) => p.id === store.activePresetId);
  deletingPresetName.value = p?.name || "未命名";
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

function showToast(msg) {
  toastMsg.value = msg;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toastMsg.value = ""; }, 2000);
}
</script>

<style scoped>
.pp-area {
  position: relative;
  padding: 8px 0;
}

.pp-row {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-bottom: 16px;
}

.pp-select {
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

.pp-btn {
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
.pp-btn:hover:not(:disabled) {
  background: #f0f0f0;
  color: #333;
}
.pp-btn:disabled {
  opacity: 0.3;
  cursor: default;
}

.pp-fields {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.pp-label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
  color: #888;
  font-weight: 500;
}

.pp-input {
  padding: 10px 12px;
  border: 1px solid #d5d5d5;
  border-radius: 8px;
  font-size: 14px;
  color: #333;
  outline: none;
  font-family: inherit;
  width: 100%;
  box-sizing: border-box;
}
.pp-input:focus {
  border-color: #4a90d9;
  box-shadow: 0 0 0 2px rgba(74, 144, 217, 0.15);
}

.pp-save-btn {
  width: 100%;
  padding: 10px 0;
  border: none;
  border-radius: 8px;
  background: #4a90d9;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s;
}
.pp-save-btn:hover:not(:disabled) {
  background: #357abd;
}
.pp-save-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

.pp-toast {
  position: absolute;
  top: -6px;
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
