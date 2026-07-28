<template>
  <div
    class="pe-item"
    :class="{ 'pe-item--dragging': isDragging }"
    :draggable="true"
    @dragstart="onDragStart"
    @dragend="onDragEnd"
    @dragover.prevent="onDragOver"
    @drop.prevent="onDrop"
  >
    <span class="pe-item__handle" title="拖拽排序">*</span>
    <span class="pe-item__name">{{ entry.name }}</span>
    <span class="pe-item__token">-</span>
    <button class="pe-item__edit" title="编辑" @click="$emit('edit', entry)">
      ✏️
    </button>
    <div
      class="pe-item__toggle toggle-switch"
      :class="{ active: entry.enabled }"
      @click="$emit('toggle', entry)"
    >
      <div class="toggle-switch__slider"></div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

const props = defineProps({
  entry: { type: Object, required: true },
});

const emit = defineEmits(["toggle", "edit", "drag-start", "drop"]);

const isDragging = ref(false);

function onDragStart(e) {
  isDragging.value = true;
  e.dataTransfer.effectAllowed = "move";
  e.dataTransfer.setData("text/plain", props.entry.id);
  emit("drag-start", props.entry);
}

function onDragEnd() {
  isDragging.value = false;
}

function onDragOver(e) {
  e.dataTransfer.dropEffect = "move";
  e.currentTarget.classList.add("pe-item--drop-target");
}

function onDrop(e) {
  e.currentTarget.classList.remove("pe-item--drop-target");
  const draggedId = e.dataTransfer.getData("text/plain");
  emit("drop", draggedId, props.entry.id);
}
</script>

<style scoped>
.pe-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-light, #e5e7eb);
  transition: background-color 0.15s;
  user-select: none;
}
.pe-item:last-child {
  border-bottom: none;
}
.pe-item--drop-target {
  border-top: 2px solid var(--color-accent, #4facfe);
}
.pe-item--dragging {
  opacity: 0.5;
}

.pe-item__handle {
  cursor: grab;
  font-size: 16px;
  color: var(--text-muted, #9ca3af);
  margin-right: 8px;
  flex-shrink: 0;
}
.pe-item__handle:active {
  cursor: grabbing;
}

.pe-item__name {
  flex: 1;
  font-size: 14px;
  color: var(--text-primary, #1f2937);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pe-item__token {
  font-size: 12px;
  color: var(--text-muted, #9ca3af);
  width: 30px;
  text-align: right;
  margin-right: 12px;
  flex-shrink: 0;
}

.pe-item__edit {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  opacity: 0.6;
  padding: 4px;
  margin-right: 8px;
  flex-shrink: 0;
}
.pe-item__edit:hover {
  opacity: 1;
}

.toggle-switch {
  width: 34px;
  height: 18px;
  background-color: #444;
  border-radius: 10px;
  position: relative;
  cursor: pointer;
  transition: background-color 0.3s;
  flex-shrink: 0;
}
.toggle-switch.active {
  background-color: var(--color-accent, #007aff);
}
.toggle-switch__slider {
  width: 14px;
  height: 14px;
  background-color: #888;
  border-radius: 50%;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 0.3s, background-color 0.3s;
}
.toggle-switch.active .toggle-switch__slider {
  transform: translateX(16px);
  background-color: #fff;
}
</style>
