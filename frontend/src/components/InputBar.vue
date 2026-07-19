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
      <button class="btn-send" @click="handleSend">
        {{ chatStore.isStreaming ? '⏸' : '▶' }}
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
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid #d5d5d5;
  background: #fff;
  color: #666;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.btn-send:hover {
  background: #f0f0f0;
}
</style>
