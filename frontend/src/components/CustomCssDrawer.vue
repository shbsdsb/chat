<template>
  <div
    class="drawer-panel"
    :class="{ open: visible, resizing: resizing }"
    :style="{ width: visible ? drawerWidth + 'px' : '0' }"
  >
    <div
      class="drawer-resizer"
      @mousedown="startResize"
      :class="{ active: resizing }"
    ></div>
    <div class="drawer-inner">
      <div class="drawer-header">
        <h3>自定义 CSS</h3>
        <button class="drawer-close" @click="$emit('close')">✕</button>
      </div>
      <div class="drawer-body">
        <!-- 预设工具栏 -->
        <div class="preset-toolbar">
          <select
            class="preset-select"
            :value="store.activeId || ''"
            @change="store.selectPreset($event.target.value)"
          >
            <option
              v-for="p in store.presets"
              :key="p.id"
              :value="p.id"
            >{{ p.name }}</option>
          </select>
          <button class="toolbar-btn" @click="handleRename" title="重命名">🖊</button>
          <button class="toolbar-btn primary" @click="handleCreate" title="新建预设">＋ 新建</button>
          <button class="toolbar-btn danger" @click="handleDelete" title="删除预设">🗑</button>
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
          <button class="footer-btn" @click="handleReset" :disabled="liveContent === savedContent">↺ 重置</button>
          <button
            class="footer-btn save"
            @click="handleSave"
            :disabled="liveContent === savedContent"
          >💾 保存</button>
        </div>
      </div>
    </div>

    <!-- 重命名弹窗 -->
    <template v-if="showRename">
      <div class="rename-overlay" @click.self="showRename = false">
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
    </template>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed } from "vue";
import { useCssPresetsStore } from "@/stores/cssPresets";
import { useResizableDrawer } from "@/composables/useResizableDrawer";
import { useAlertStore } from "@/stores/alert";

const props = defineProps({
  visible: { type: Boolean, default: false },
});
const emit = defineEmits(["close"]);

const store = useCssPresetsStore();
const alert = useAlertStore();

const { width: drawerWidth, isResizing: resizing, startResize } = useResizableDrawer({
  direction: "right",
  minWidth: 320,
  maxWidth: 800,
  defaultWidth: 480,
});

// ── 实时编辑状态 ──────────────────────────────
const liveContent = ref("");
const textareaRef = ref(null);

// 抽屉打开或预设切换时，同步内容
watch(
  () => [props.visible, store.activeId],
  () => {
    liveContent.value = store.activeContent;
  },
  { immediate: true }
);

const savedContent = computed(() => store.activeContent);

function onInput(e) {
  liveContent.value = e.target.value;
  store.updateLiveCss(e.target.value);
}

// ── 操作 ─────────────────────────────────────

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
  try {
    await store.deletePreset(preset.id);
    liveContent.value = store.activeContent;
    alert.show("已删除", "success");
  } catch (e) {
    alert.show(e.message || "删除失败", "error");
  }
}

// ── 重命名 ──────────────────────────────────

const showRename = ref(false);
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

<style>
@import "@/assets/drawer.css";
</style>

<style scoped>

.drawer-inner {
  flex: 1;
  background: #fff;
  border-left: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}
.drawer-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}
.drawer-close {
  border: none;
  background: none;
  font-size: 16px;
  cursor: pointer;
  color: #999;
}
.drawer-close:hover { color: #333; }

.drawer-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px 20px;
  overflow: hidden;
}

/* 预设工具栏 */
.preset-toolbar {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
  flex-shrink: 0;
}
.preset-select {
  flex: 1;
  padding: 5px 8px;
  border: 1px solid #d5d5d5;
  border-radius: 6px;
  font-size: 13px;
  background: #fff;
}
.toolbar-btn {
  padding: 4px 8px;
  border: 1px solid #d5d5d5;
  border-radius: 6px;
  background: #fff;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
}
.toolbar-btn:hover { background: #f0f0f0; }
.toolbar-btn.primary { color: #4a90d9; border-color: #4a90d9; }
.toolbar-btn.danger { color: #e05555; border-color: #e05555; }

/* CSS 编辑器 */
.css-textarea {
  flex: 1;
  width: 100%;
  padding: 14px;
  border: 1px solid #d5d5d5;
  border-radius: 6px;
  font-family: "Consolas", "Monaco", "Courier New", monospace;
  font-size: 13px;
  line-height: 1.6;
  resize: none;
  outline: none;
  background: #1e1e1e;
  color: #d4d4d4;
  tab-size: 2;
}
.css-textarea:focus {
  border-color: #4a90d9;
}
.css-textarea::placeholder {
  color: #666;
}

/* 底部按钮 */
.footer-btns {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
  flex-shrink: 0;
}
.footer-btn {
  padding: 6px 16px;
  border: 1px solid #d5d5d5;
  border-radius: 6px;
  background: #fff;
  font-size: 13px;
  cursor: pointer;
}
.footer-btn:hover:not(:disabled) { background: #f0f0f0; }
.footer-btn:disabled { opacity: 0.4; cursor: default; }
.footer-btn.save {
  background: #4a90d9;
  color: #fff;
  border-color: #4a90d9;
}
.footer-btn.save:hover:not(:disabled) { background: #3a7bc8; }

/* 重命名弹窗 */
.rename-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.rename-dialog {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 260px;
}
.rename-dialog input {
  padding: 8px 12px;
  border: 1px solid #d5d5d5;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
}
.rename-dialog input:focus { border-color: #4a90d9; }
.rename-btns {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.rename-btns button {
  padding: 5px 14px;
  border: 1px solid #d5d5d5;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
}
.rename-btns button:first-child {
  background: #4a90d9;
  color: #fff;
  border-color: #4a90d9;
}
</style>
