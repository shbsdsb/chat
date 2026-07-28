<template>
  <div class="card">
    <div class="card-header">
      <span class="card-icon"><Palette :size="18" /></span>
      <span class="card-label">CSS 主题</span>
    </div>

    <!-- 预设工具栏 -->
    <div class="preset-toolbar">
      <select
        class="input-field"
        style="flex:1;min-width:140px;"
        :value="store.activeId || ''"
        @change="store.selectPreset($event.target.value)"
      >
        <option v-for="p in store.presets" :key="p.id" :value="p.id">{{ p.name }}</option>
      </select>
      <button class="icon-btn" @click="handleRename" title="重命名"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3a2.83 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg></button>
      <button class="btn-sm primary" @click="handleCreate">+ 新建</button>
      <button class="icon-btn danger" @click="handleDelete" title="删除预设"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg></button>
    </div>

    <!-- CSS 编辑器 -->
    <textarea
      ref="textareaRef"
      class="css-textarea"
      :value="liveContent"
      @input="onInput"
      placeholder="/* 输入自定义 CSS */&#10;body {&#10;  background: #fff;&#10;}"
      spellcheck="false"
    ></textarea>

    <!-- 操作按钮 -->
    <div class="footer-btns">
      <button class="btn-sm outline" @click="handleReset" :disabled="liveContent === savedContent">↺ 重置</button>
      <button class="btn-sm primary" @click="handleSave" :disabled="liveContent === savedContent">保存</button>
    </div>

    <!-- 重命名弹窗 -->
    <div v-if="showRename" class="rename-overlay" @click.self="showRename = false">
      <div class="rename-dialog">
        <input
          ref="renameInputRef"
          v-model="renameValue"
          @keydown.enter="confirmRename"
          @keydown.escape="showRename = false"
          placeholder="预设名称"
        />
        <div class="rename-btns">
          <button @click="confirmRename">确定</button>
          <button @click="showRename = false">取消</button>
        </div>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <BaseDialog :visible="showDeleteConfirm" title="删除预设" @close="showDeleteConfirm = false">
      <p class="dialog-danger-msg">确定要删除预设「{{ store.activePreset?.name }}」吗？此操作不可撤销。</p>
      <template #footer>
        <button class="dialog-btn dialog-btn-cancel" @click="showDeleteConfirm = false">取消</button>
        <button class="dialog-btn dialog-btn-danger" @click="confirmDelete">确定删除</button>
      </template>
    </BaseDialog>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed } from "vue";
import { Palette } from "lucide-vue-next";
import { useCssPresetsStore } from "@/stores/cssPresets";
import { useAlertStore } from "@/stores/alert";
import BaseDialog from "@/components/BaseDialog.vue";

const store = useCssPresetsStore();
const alert = useAlertStore();

const liveContent = ref("");
const textareaRef = ref(null);

watch(
  () => store.activeId,
  () => { liveContent.value = store.activeContent; },
  { immediate: true }
);

const savedContent = computed(() => store.activeContent);

function onInput(e) {
  liveContent.value = e.target.value;
  store.updateLiveCss(e.target.value);
}

async function handleSave() {
  try {
    const preset = store.activePreset;
    if (!preset) return;
    await store.savePreset(preset.name, liveContent.value);
    alert.show("CSS 保存成功", "success");
  } catch (e) {
    alert.show(e.message || "保存失败", "error");
  }
}

function handleReset() {
  liveContent.value = store.activeContent;
  store.updateLiveCss(store.activeContent);
}

async function handleCreate() {
  try {
    await store.createPreset("未命名");
    await nextTick();
    liveContent.value = "";
  } catch (e) {
    alert.show(e.message || "创建失败", "error");
  }
}

async function handleDelete() {
  const preset = store.activePreset;
  if (!preset) return;
  if (preset.is_default) {
    alert.show("不能删除默认CSS预设，请先切换默认预设", "error");
    return;
  }
  showDeleteConfirm.value = true;
}

async function confirmDelete() {
  const preset = store.activePreset;
  if (!preset) return;
  try {
    await store.deletePreset(preset.id);
    liveContent.value = store.activeContent;
    showDeleteConfirm.value = false;
    alert.show("已删除", "success");
  } catch (e) {
    alert.show(e.message || "删除失败", "error");
  }
}

// ── 重命名 ──────────────────────────────────

const showRename = ref(false);
const showDeleteConfirm = ref(false);
const renameValue = ref("");
const renameInputRef = ref(null);

function handleRename() {
  const preset = store.activePreset;
  if (!preset) return;
  renameValue.value = preset.name;
  showRename.value = true;
  nextTick(() => renameInputRef.value?.focus());
}

async function confirmRename() {
  const name = renameValue.value.trim();
  if (!name) return;
  try {
    await store.savePreset(name, liveContent.value);
    showRename.value = false;
    alert.show("重命名成功", "success");
  } catch (e) {
    alert.show(e.message || "重命名失败", "error");
  }
}
</script>

<style scoped>
/* ——— 卡片 ——— */
.card { background: var(--bg-primary); border: 1px solid var(--border); border-radius: var(--radius-lg); box-shadow: var(--shadow-sm); padding: 16px 18px; display: flex; flex-direction: column; height: 100%; }
.card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.card-icon { color: var(--accent); display: flex; align-items: center; width: 20px; height: 20px; }
.card-label { font-size: 13px; font-weight: 600; color: var(--text-secondary); }

/* ——— 按钮 ——— */
.btn-sm { display: inline-flex; align-items: center; gap: 5px; padding: 7px 14px; border: none; border-radius: var(--radius-sm); font-size: 12px; font-weight: 600; cursor: pointer; font-family: inherit; white-space: nowrap; transition: all 0.15s; }
.btn-sm.primary { background: var(--accent); color: #fff; box-shadow: 0 1px 3px rgba(79,110,246,0.2); }
.btn-sm.primary:hover:not(:disabled) { background: var(--accent-light); transform: translateY(-1px); box-shadow: 0 2px 6px rgba(79,110,246,0.3); }
.btn-sm.outline { background: var(--bg-input); color: var(--text-secondary); border: 1px solid var(--border-light); }
.btn-sm.outline:hover:not(:disabled) { color: var(--text-primary); border-color: var(--border); background: var(--bg-input-hover); }
.btn-sm:disabled { opacity: 0.45; cursor: default; transform: none; box-shadow: none; }
.icon-btn { width: 32px; height: 32px; border: 1px solid var(--border-light); border-radius: var(--radius-sm); background: var(--bg-input); color: var(--text-secondary); cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: all 0.15s; }
.icon-btn:hover { color: var(--text-primary); border-color: var(--border); background: var(--bg-input-hover); }
.icon-btn.danger:hover { color: var(--danger); border-color: var(--danger); background: var(--danger-bg); }

/* ——— 输入 ——— */
.input-field { width: 100%; padding: 7px 10px; border: 1px solid var(--border-light); border-radius: var(--radius-sm); font-size: 13px; color: var(--text-primary); background: var(--bg-input); outline: none; font-family: inherit; transition: border-color 0.15s, box-shadow 0.15s; }
.input-field:focus { border-color: var(--accent); box-shadow: var(--focus-ring); }

/* ——— 工具栏 ——— */
.preset-toolbar { display: flex; align-items: center; gap: 6px; margin-bottom: 12px; flex-shrink: 0; }

/* ——— 编辑器 ——— */
.css-textarea { flex: 1; width: 100%; padding: 14px; border: 1px solid var(--border-light); border-radius: var(--radius-sm); font-family: "Consolas", "Monaco", "Courier New", monospace; font-size: 13px; line-height: 1.6; resize: none; outline: none; background: #1e1e1e; color: #d4d4d4; tab-size: 2; transition: border-color 0.15s, box-shadow 0.15s; }
.css-textarea:focus { border-color: var(--accent); box-shadow: var(--focus-ring); }
.css-textarea::placeholder { color: #666; }

/* ——— 底部按钮 ——— */
.footer-btns { display: flex; justify-content: flex-end; gap: 8px; margin-top: 12px; flex-shrink: 0; }

/* ——— 重命名弹窗 ——— */
.rename-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.rename-dialog { background: var(--bg-primary); padding: 20px; border-radius: var(--radius-md); box-shadow: var(--shadow-md); display: flex; flex-direction: column; gap: 12px; min-width: 260px; }
.rename-dialog input { padding: 8px 12px; border: 1px solid var(--border-light); border-radius: var(--radius-sm); font-size: 14px; outline: none; background: var(--bg-input); color: var(--text-primary); }
.rename-dialog input:focus { border-color: var(--accent); box-shadow: var(--focus-ring); }
.rename-btns { display: flex; justify-content: flex-end; gap: 8px; }
.rename-btns button { padding: 5px 14px; border: 1px solid var(--border-light); border-radius: var(--radius-sm); background: var(--bg-input); cursor: pointer; font-size: 13px; color: var(--text-secondary); }
.rename-btns button:first-child { background: var(--accent); color: #fff; border-color: var(--accent); }
</style>
