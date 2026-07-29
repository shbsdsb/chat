<template>
  <div class="card">
    <div class="card-header">
      <span class="card-icon"><List :size="18" /></span>
      <span class="card-label">提示词条目</span>
      <button class="icon-btn" title="添加条目" @click="showAddInput = true"
        v-if="!showAddInput"
      >+</button>
    </div>

    <!-- 新增输入行 -->
    <div v-if="showAddInput" class="pe-add-row">
      <input
        ref="addInputRef"
        v-model="newName"
        class="input-field"
        placeholder="输入条目名称，回车确认"
        @keydown.enter="handleAdd"
        @keydown.escape="cancelAdd"
        @blur="cancelAdd"
      />
    </div>

    <!-- 空状态 -->
    <div v-if="!store.loading && entries.length === 0 && !showAddInput" class="pe-empty">
      暂无条目，点击 + 创建
    </div>

    <!-- 条目列表 -->
    <div v-if="entries.length > 0" class="pe-list" ref="listRef">
      <PromptEntryItem
        v-for="(entry, idx) in entries"
        :key="entry.id"
        :entry="entry"
        :dragging="dragging && dragIndex === idx"
        :style="{ transform: getDragTransform(idx) }"
        @toggle="handleToggle"
        @edit="openEditModal(entry)"
        @drag-start="onItemMouseDown(entry, $event)"
      />
    </div>

    <!-- 编辑 Modal -->
    <PromptEntryModal
      :visible="showEditModal"
      :entry="editingEntry"
      @close="showEditModal = false"
      @save="handleEditSave"
      @delete="handleEditDelete"
    />
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed, onBeforeUnmount } from "vue";
import { List } from "lucide-vue-next";
import { usePresetsStore } from "@/stores/presets";
import PromptEntryItem from "@/components/PromptEntryItem.vue";
import PromptEntryModal from "@/components/PromptEntryModal.vue";

const store = usePresetsStore();

const showAddInput = ref(false);
const newName = ref("");
const addInputRef = ref(null);
const listRef = ref(null);

// 编辑 Modal
const showEditModal = ref(false);
const editingEntry = ref({});

// ---- 拖拽状态 ----
const dragging = ref(false);
const dragIndex = ref(-1);
const targetIndex = ref(-1);
const offsetY = ref(0);
let startY = 0;
let itemHeight = 0;

const entries = computed(() => store.entriesList);

function getItemHeight() {
  if (!listRef.value) return 49;
  const first = listRef.value.children[0];
  if (!first) return 49;
  return first.getBoundingClientRect().height;
}

function getDragTransform(idx) {
  if (!dragging.value) return "translateY(0)";
  const di = dragIndex.value;
  const ti = targetIndex.value;
  if (di === -1) return "translateY(0)";

  const h = itemHeight || getItemHeight();
  if (idx === di) {
    // 被拖拽项只跟随鼠标偏移，不额外增加目标位置偏移
    return `translateY(${offsetY.value}px)`;
  }
  // 其他项挤压
  if (di < ti && idx > di && idx <= ti) return `translateY(-${h}px)`;
  if (di > ti && idx >= ti && idx < di) return `translateY(${h}px)`;
  return "translateY(0)";
}

function onItemMouseDown(entry, event) {
  if (event.button !== 0) return;

  const idx = entries.value.findIndex((e) => e.id === entry.id);
  if (idx === -1) return;

  dragging.value = true;
  dragIndex.value = idx;
  targetIndex.value = idx;
  startY = event.clientY;
  itemHeight = getItemHeight();

  // 初始偏移：让被拖拽条目从鼠标位置开始
  const h = itemHeight;
  const rect = listRef.value.getBoundingClientRect();
  const relativeY = event.clientY - rect.top;
  offsetY.value = relativeY - idx * h - h / 2;

  document.addEventListener("mousemove", onMouseMove);
  document.addEventListener("mouseup", onMouseUp);
}

function onMouseMove(e) {
  if (!dragging.value) return;

  const h = itemHeight || getItemHeight();
  const rect = listRef.value.getBoundingClientRect();
  const relativeY = e.clientY - rect.top;
  const n = entries.value.length;

  let newTarget = Math.floor(relativeY / h);
  newTarget = Math.max(0, Math.min(newTarget, n - 1));

  offsetY.value = relativeY - dragIndex.value * h - h / 2;
  targetIndex.value = newTarget;
}

function onMouseUp() {
  if (!dragging.value) return;

  document.removeEventListener("mousemove", onMouseMove);
  document.removeEventListener("mouseup", onMouseUp);

  const di = dragIndex.value;
  const ti = targetIndex.value;

  // 直接操作 DOM：冻结所有条目，瞬间落位
  const items = listRef.value?.querySelectorAll(".pe-item");
  if (items) {
    items.forEach((el) => {
      el.style.transition = "none";
      el.style.transform = "translateY(0)";
    });
    // 强制同步重排，确保样式立即生效
    void listRef.value.offsetHeight;
  }

  dragging.value = false;
  dragIndex.value = -1;
  targetIndex.value = -1;
  offsetY.value = 0;

  if (di !== ti && di >= 0 && ti >= 0) {
    const data = [...store.entriesList];
    const [moved] = data.splice(di, 1);
    data.splice(ti, 0, moved);

    // 重新分配 order（含 __chat_history__，保留其拖拽后的位置）
    data.forEach((e, i) => { e.order = i; });
    const orderedIds = data.map(e => e.id);
    store.reorderEntries(orderedIds);
  }

  // 下一帧恢复 transition
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      if (items) {
        items.forEach((el) => {
          el.style.transition = "";
          el.style.transform = "";
        });
      }
    });
  });
}

onBeforeUnmount(() => {
  document.removeEventListener("mousemove", onMouseMove);
  document.removeEventListener("mouseup", onMouseUp);
});

// ---- 预设切换 ----
watch(
  () => store.activePresetId,
  (newId) => {
    if (newId) store.selectPreset(newId);
  },
  { immediate: true }
);

// ---- 输入框自动聚焦 ----
watch(showAddInput, async (val) => {
  if (val) {
    await nextTick();
    addInputRef.value?.focus();
  }
});

async function handleAdd() {
  const name = newName.value.trim();
  if (!name) return;
  store.addEntry(name);
  newName.value = "";
  showAddInput.value = false;
}

function cancelAdd() {
  newName.value = "";
  showAddInput.value = false;
}

async function handleToggle(entry) {
  store.updateEntry(entry.id, { enabled: !entry.enabled });
}

function openEditModal(entry) {
  // 防御：chat_history 不可编辑（编辑按钮已隐藏，兜底）
  if (entry.id === "__chat_history__") return;
  editingEntry.value = { ...entry };
  showEditModal.value = true;
}

async function handleEditSave({ name, content, role }) {
  store.updateEntry(editingEntry.value.id, { name, content, role });
  showEditModal.value = false;
}

async function handleEditDelete(id) {
  store.removeEntry(id);
  showEditModal.value = false;
}
</script>

<style scoped>
.card {
  background: var(--bg-card, #fff);
  border-radius: var(--radius-card, 16px);
  box-shadow: var(--shadow-sm, 0 1px 3px rgba(0, 0, 0, 0.08));
  padding: 16px 20px;
  margin-top: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.card-icon {
  display: flex;
  align-items: center;
  color: var(--accent, #4f6ef6);
}

.card-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #1f2937);
  flex: 1;
}

.icon-btn {
  background: none;
  border: 1px solid var(--border-light, #e5e7eb);
  border-radius: 6px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 16px;
  color: var(--text-secondary, #6b7280);
  transition: background-color 0.15s;
}
.icon-btn:hover {
  background: var(--bg-hover, #f3f4f6);
}

.pe-add-row {
  margin-bottom: 8px;
}

.input-field {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-light, #e5e7eb);
  border-radius: 8px;
  font-size: 14px;
  background: var(--bg-input, #fafbfc);
  color: var(--text-primary, #1f2937);
  outline: none;
  box-sizing: border-box;
}
.input-field:focus {
  border-color: var(--focus-ring, #4facfe);
  box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.15);
}

.pe-empty {
  text-align: center;
  padding: 20px 0;
  color: var(--text-muted, #9ca3af);
  font-size: 13px;
}
</style>
