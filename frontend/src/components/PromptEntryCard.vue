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
    <div v-if="!store.loading && store.entries.length === 0 && !showAddInput" class="pe-empty">
      暂无条目，点击 + 创建
    </div>

    <!-- 条目列表 -->
    <div v-if="store.entries.length > 0" class="pe-list">
      <PromptEntryItem
        v-for="entry in store.entries"
        :key="entry.id"
        :entry="entry"
        :style="getItemStyle(entry)"
        @toggle="handleToggle"
        @drag-start="onDragStart"
        @drag-over="onDragOver"
        @drag-end="resetDrag"
        @drop="onDrop"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from "vue";
import { List } from "lucide-vue-next";
import { usePromptEntriesStore } from "@/stores/promptEntries";
import { useParamPresetsStore } from "@/stores/paramPresets";
import PromptEntryItem from "@/components/PromptEntryItem.vue";

const store = usePromptEntriesStore();
const paramStore = useParamPresetsStore();

const showAddInput = ref(false);
const newName = ref("");
const addInputRef = ref(null);
const draggedId = ref(null);
const overTargetId = ref(null);
const overPosition = ref("after");

const ITEM_HEIGHT = 49;

// 切换参数预设时重新加载条目
watch(
  () => paramStore.activePresetId,
  (newId) => {
    store.loadEntries(newId);
  },
  { immediate: true }
);

// 打开输入框时自动聚焦
watch(showAddInput, async (val) => {
  if (val) {
    await nextTick();
    addInputRef.value?.focus();
  }
});

async function handleAdd() {
  const name = newName.value.trim();
  if (!name) return;
  await store.createEntry(name);
  newName.value = "";
  showAddInput.value = false;
}

function cancelAdd() {
  newName.value = "";
  showAddInput.value = false;
}

async function handleToggle(entry) {
  await store.updateEntry(entry.id, { enabled: !entry.enabled });
}

function onDragStart(entry) {
  draggedId.value = entry.id;
}

function onDragOver(id, position) {
  overTargetId.value = id;
  overPosition.value = position;
}

function getItemStyle(entry) {
  if (!draggedId.value || !overTargetId.value) return {};
  if (entry.id === draggedId.value) return {};

  const entries = store.entries;
  const dragIdx = entries.findIndex((e) => e.id === draggedId.value);
  const overIdx = entries.findIndex((e) => e.id === overTargetId.value);
  const entryIdx = entries.findIndex((e) => e.id === entry.id);
  if (dragIdx === -1 || overIdx === -1) return {};
  if (dragIdx === overIdx) return {};

  const insertBefore = overPosition.value === "before";
  const splitPoint = insertBefore ? overIdx : overIdx + 1;

  if (dragIdx < splitPoint) {
    // 源在上，目标在下
    if (entryIdx > dragIdx && entryIdx < splitPoint) {
      return { transform: `translateY(-${ITEM_HEIGHT}px)` };
    }
  } else {
    // 源在下，目标在上
    if (entryIdx >= splitPoint && entryIdx < dragIdx) {
      return { transform: `translateY(${ITEM_HEIGHT}px)` };
    }
  }
  return {};
}

function onDrop(draggedEntryId, targetId) {
  const entries = [...store.entries];
  const dragIdx = entries.findIndex((e) => e.id === draggedEntryId);
  let targetIdx = entries.findIndex((e) => e.id === targetId);
  if (dragIdx === -1 || targetIdx === -1 || dragIdx === targetIdx) {
    resetDrag();
    return;
  }

  const [moved] = entries.splice(dragIdx, 1);
  // 重新计算 targetIdx（因为 splice 后索引可能变了）
  targetIdx = entries.findIndex((e) => e.id === targetId);
  let insertAt = targetIdx;
  if (overPosition.value === "after") insertAt = targetIdx + 1;
  entries.splice(insertAt, 0, moved);

  resetDrag();
  store.reorderEntries(entries.map((e) => e.id));
}

function resetDrag() {
  draggedId.value = null;
  overTargetId.value = null;
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

.pe-list {
  /* 条目容器 */
}
</style>
