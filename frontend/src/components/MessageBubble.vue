<template>
  <div class="bubble-row" :class="message.role">
    <div class="bubble">
      <div
        v-if="message.role === 'assistant' && message.reasoning_content"
        class="reasoning-block"
      >
        <div class="reasoning-header" @click="reasoningOpen = !reasoningOpen">
          <span class="reasoning-icon">{{ reasoningOpen ? '▼' : '▶' }}</span>
          <span>思考过程</span>
        </div>
        <div v-show="reasoningOpen" class="reasoning-content">
          {{ message.reasoning_content }}
        </div>
      </div>
      <div class="bubble-text">{{ message.content }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

defineProps({
  message: { type: Object, required: true },
});

const reasoningOpen = ref(true);
</script>

<style scoped>
.bubble-row {
  display: flex;
  margin-bottom: 12px;
}
.bubble-row.user {
  justify-content: flex-end;
}
.bubble-row.assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid #e0e0e0;
  background: #fff;
  color: #333;
  font-size: 15px;
  line-height: 1.6;
}
.bubble-row.user .bubble {
  border-color: #d5d5d5;
}
.bubble-row.assistant .bubble {
  border-color: #e8e8e8;
}

.bubble-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.reasoning-block {
  margin-bottom: 10px;
  border-left: 2px solid #d0d0d0;
  padding-left: 10px;
}

.reasoning-header {
  cursor: pointer;
  font-size: 13px;
  color: #888;
  user-select: none;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 4px;
}

.reasoning-header:hover {
  color: #666;
}

.reasoning-icon {
  font-size: 10px;
  width: 12px;
}

.reasoning-content {
  font-size: 13px;
  color: #999;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
}
</style>
