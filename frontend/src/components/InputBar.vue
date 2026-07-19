<template>
  <div class="input-bar">
    <div class="input-wrapper">
      <textarea
        v-model="input"
        class="input-field"
        placeholder="输入消息..."
        rows="1"
        @keydown.enter.exact.prevent="handleSend"
      ></textarea>
      <button
        class="btn-send"
        :class="{ 'is-streaming': chatStore.isStreaming }"
        @click="handleSend"
        :title="chatStore.isStreaming ? '停止生成' : '发送'"
      >
        <!-- 纸飞机 (Telegram 风格) -->
        <svg
          v-if="!chatStore.isStreaming"
          class="icon-send"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M22 2L11 13" />
          <path d="M22 2L15 22L11 13L2 9L22 2Z" />
        </svg>
        <!-- 停止方块 -->
        <svg
          v-else
          class="icon-stop"
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <rect x="6" y="6" width="12" height="12" rx="2" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useChatStore } from "@/stores/chat";

const chatStore = useChatStore();
const input = ref("");

function handleSend() {
  if (chatStore.isStreaming) {
    chatStore.stopStreaming();
    return;
  }
  const text = input.value.trim();
  if (!text) return;
  chatStore.sendMessage(text);
  input.value = "";
}
</script>

<style scoped>
.input-bar {
  padding: 12px 24px 16px;
  border-top: 1px solid #f0f0f0;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  border: 1px solid #d5d5d5;
  border-radius: 24px;
  padding: 6px 6px 6px 16px;
  background: #fff;
}

.input-field {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: 15px;
  line-height: 1.5;
  max-height: 120px;
  padding: 4px 0;
  font-family: inherit;
}
.input-field::placeholder {
  color: #bbb;
}

.btn-send {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: #0088cc;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.2s, transform 0.15s;
}
.btn-send:hover {
  background: #0077b5;
  transform: scale(1.05);
}
.btn-send:active {
  transform: scale(0.95);
}
.btn-send.is-streaming {
  background: #e53935;
}
.btn-send.is-streaming:hover {
  background: #c62828;
}

.icon-send {
  width: 18px;
  height: 18px;
  margin-left: 1px; /* 视觉居中微调 */
}

.icon-stop {
  width: 14px;
  height: 14px;
}
</style>
