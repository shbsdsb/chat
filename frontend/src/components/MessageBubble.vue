<template>
  <div class="bubble-row" :class="message.role">
    <div class="bubble">
      <div class="bubble-text">{{ message.content }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  message: { type: Object, required: true },
});
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
</style>
