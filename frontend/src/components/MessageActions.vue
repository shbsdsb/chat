<template>
  <div class="message-actions">
    <button class="action-btn" title="编辑" @click="$emit('edit', message.id)">✎</button>
    <button class="action-btn replay-btn" title="重新生成" @click="$emit('replay', message.id)">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.13-9.36L23 10"/></svg>
    </button>
    <template v-if="totalVersions > 1">
      <button class="action-btn" title="上一个版本" @click="$emit('prev', message.id)">←</button>
      <span class="version-badge">{{ versionIndex + 1 }} / {{ totalVersions }}</span>
      <button class="action-btn" title="下一个版本" @click="$emit('next', message.id)">→</button>
    </template>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useChatStore } from "@/stores/chat";

const props = defineProps({
  message: { type: Object, required: true },
});
defineEmits(["edit", "replay", "prev", "next"]);

const chatStore = useChatStore();

const versions = computed(() => chatStore.aiVersions[props.message.id] || []);
const totalVersions = computed(() => versions.value.length);
const versionIndex = computed(() => {
  if (totalVersions.value <= 1) return 0;
  return chatStore.aiVersionIndex;
});
</script>

<style scoped>
.message-actions {
  display: flex;
  gap: 4px;
  align-items: center;
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

.replay-btn {
  border-color: #d5d5d5;
  background: #fff;
  color: #666;
}
.replay-btn:hover {
  background: #f0f0f0;
  color: #333;
}

.version-badge {
  font-size: 12px;
  color: #aaa;
  min-width: 36px;
  text-align: center;
  user-select: none;
}
</style>
