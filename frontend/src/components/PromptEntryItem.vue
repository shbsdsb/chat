<template>
  <div
    class="pe-item"
    :class="{
      'pe-item--dragging': dragging,
      'pe-item--chat-history': entry.id === '__chat_history__',
    }"
  >
    <span class="pe-item__handle" title="拖拽排序" @mousedown.prevent="$emit('drag-start', $event)">
      <svg width="18" height="18" viewBox="0 0 100 100">
        <g stroke="currentColor" stroke-width="14" stroke-linecap="round" stroke-linejoin="round">
          <line x1="50" y1="16" x2="50" y2="84"/>
          <line x1="20" y1="32" x2="80" y2="68"/>
          <line x1="80" y1="32" x2="20" y2="68"/>
        </g>
      </svg>
    </span>
    <span class="pe-item__name">{{ entry.name }}</span>
    <span class="pe-item__token">{{ entry.id === '__chat_history__' ? '' : '-' }}</span>
    <button
      v-if="entry.id !== '__chat_history__'"
      class="pe-item__edit"
      title="编辑"
      @click="$emit('edit', entry)"
    >
      <Pencil :size="14" />
    </button>
    <div
      v-if="entry.id !== '__chat_history__'"
      class="pe-item__toggle toggle-switch"
      :class="{ active: entry.enabled }"
      @click="$emit('toggle', entry)"
    >
      <div class="toggle-switch__slider"></div>
    </div>
  </div>
</template>

<script setup>
import { Pencil } from "lucide-vue-next";

defineProps({
  entry: { type: Object, required: true },
  dragging: { type: Boolean, default: false },
});

defineEmits(["toggle", "edit", "drag-start"]);
</script>

<style scoped>
.pe-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-light, #e5e7eb);
  transition: transform 0.22s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.2s ease;
  user-select: none;
  will-change: transform;
  transform: translateY(0);
}
.pe-item:last-child {
  border-bottom: none;
}
.pe-item--dragging {
  opacity: 0.35;
}

.pe-item__handle {
  cursor: grab;
  color: var(--text-muted, #9ca3af);
  margin-right: 8px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
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
  color: var(--text-muted, #9ca3af);
  opacity: 0.6;
  padding: 4px;
  margin-right: 8px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
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

/* chat_history 特殊条目 */
.pe-item--chat-history {
  color: var(--text-muted, #9ca3af);
  font-style: italic;
  opacity: 0.8;
}
.pe-item--chat-history .pe-item__name::before {
  content: "💬 ";
}
</style>
