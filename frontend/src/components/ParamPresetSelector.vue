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

    <!-- 删除确认弹窗 -->
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

<script setup>
import { ref, reactive, watch, nextTick } from "vue";
import { SlidersHorizontal } from "lucide-vue-next";
import { useParamPresetsStore } from "@/stores/paramPresets";
import { useAlertStore } from "@/stores/alert";
import BaseDialog from "@/components/BaseDialog.vue";

const store = useParamPresetsStore();
const alert = useAlertStore();
const emit = defineEmits(["saved"]);

const toastMsg = ref("");
let toastTimer = null;

const form = reactive({ temperature: 0.7, maxTokens: 4096, topP: 1.0 });

watch(() => store.activePresetId, (id) => {
  const p = store.presets.find((p) => p.id === id);
  if (p) { form.temperature = p.temperature; form.maxTokens = p.max_tokens; form.topP = p.top_p; }
});

function onSelect() {}

const showNameDialog = ref(false);
const dialogName = ref("");
const nameInput = ref(null);

function clearForm() {
  store.activePresetId = null;
  form.temperature = 0.7; form.maxTokens = 4096; form.topP = 1.0;
  let base = "新预设", candidate = base, n = 1;
  while (store.presets.some((p) => p.name === candidate)) { candidate = `${base} (${n})`; n++; }
  dialogName.value = candidate;
  showNameDialog.value = true;
  nextTick(() => { nameInput.value?.focus(); nameInput.value?.select(); });
}

async function confirmNameDialog() {
  const name = dialogName.value.trim();
  if (!name) return;
  showNameDialog.value = false;
  try { await store.createPreset(name, form.temperature, form.maxTokens, form.topP); showToast("预设已创建"); emit("saved"); }
  catch (e) { alert.error("创建失败", e.message || "未知错误"); }
}

function cancelNameDialog() { showNameDialog.value = false; dialogName.value = ""; }

async function handleSave() {
  if (!store.activePresetId) return;
  try { await store.savePreset(form.temperature, form.maxTokens, form.topP); showToast("保存成功"); }
  catch (e) { alert.error("保存失败", e.message || "未知错误"); }
}

const showDeleteDialog = ref(false);
const deletingPresetName = ref("");

function handleDelete() {
  const p = store.presets.find((p) => p.id === store.activePresetId);
  deletingPresetName.value = p?.name || "未命名";
  showDeleteDialog.value = true;
}

async function confirmDelete() {
  showDeleteDialog.value = false;
  try { await store.deletePreset(store.activePresetId); showToast("已删除"); } catch (e) { alert.error("删除失败", e.message || "未知错误"); }
}

function cancelDelete() { showDeleteDialog.value = false; }

function showToast(msg) { toastMsg.value = msg; clearTimeout(toastTimer); toastTimer = setTimeout(() => { toastMsg.value = ""; }, 2000); }
</script>

<style>
.card {
  background: var(--bg-primary); border: 1px solid var(--border);
  border-radius: var(--radius-lg); box-shadow: var(--shadow-sm);
  padding: 16px 18px; display: flex; flex-direction: column;
}
.card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; }
.card-icon { color: var(--accent); display: flex; align-items: center; width: 20px; height: 20px; }
.card-label { font-size: 13px; font-weight: 600; color: var(--text-secondary); }

.pp-row { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; margin-bottom: 14px; }

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

.icon-btn {
  width: 32px; height: 32px; border: 1px solid var(--border-light);
  border-radius: var(--radius-sm); background: var(--bg-input); color: var(--text-secondary);
  cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  transition: all 0.15s; font-size: 16px; line-height: 1;
}
.icon-btn:hover:not(:disabled) { color: var(--text-primary); border-color: var(--border); background: var(--bg-input-hover); }
.icon-btn.danger:hover:not(:disabled) { color: var(--danger); border-color: var(--danger); background: var(--danger-bg); }
.icon-btn:disabled { opacity: 0.45; cursor: default; }

.btn-save {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 18px; border: none; border-radius: var(--radius-sm);
  background: var(--accent); color: #fff; font-size: 13px; font-weight: 600;
  cursor: pointer; font-family: inherit;
  box-shadow: 0 1px 3px rgba(79,110,246,0.2); transition: all 0.15s;
}
.btn-save:hover:not(:disabled) { background: var(--accent-light); transform: translateY(-1px); box-shadow: 0 2px 6px rgba(79,110,246,0.3); }
.btn-save:disabled { opacity: 0.45; cursor: default; transform: none; box-shadow: none; }

.pp-toast {
  position: absolute; top: -6px; left: 0;
  font-size: 12px; color: var(--text-secondary);
  background: var(--bg-input); padding: 3px 10px;
  border-radius: var(--radius-sm); white-space: nowrap; pointer-events: none;
}
.fade-enter-active, .fade-leave-active { transition: opacity 0.25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
