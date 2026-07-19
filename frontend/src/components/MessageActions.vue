<template>
  <div class="message-actions">
    <button class="action-btn" title="编辑" @click="$emit('edit', message.id)">✎</button>
    <button class="action-btn" title="重放" @click="$emit('replay', message.id)">🔄</button>
    <button class="action-btn" title="上一个版本" @click="$emit('prev', message.id)">←</button>
    <button class="action-btn" title="下一个版本" @click="$emit('next', message.id)">→</button>
  </div>
</template>

<script setup>
defineProps({
  message: { type: Object, required: true },
});
defineEmits(["edit", "replay", "prev", "next"]);
</script>

<style scoped>
.message-actions {
  display: flex;
  gap: 4px;
  padding-left: 4px;
  margin-bottom: 12px;
}

.action-btn {
  width: 28px;
  height: 28px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #fafafa;
  color: #888;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.action-btn:hover {
  background: #e8e8e8;
  color: #555;
}
</style>
