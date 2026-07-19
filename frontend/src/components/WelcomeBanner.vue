<template>
  <div class="welcome">
    <h1>Chat</h1>
    <p>选择一个对话开始，或创建一个新对话</p>
    <button class="btn-start" @click="chatStore.createConversation()">开始新对话</button>
  </div>
</template>

<script setup>
import { useChatStore } from "@/stores/chat";
const chatStore = useChatStore();
</script>

<style scoped>
.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
}
.welcome h1 {
  font-size: 28px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}
.welcome p {
  font-size: 15px;
  margin-bottom: 24px;
}
.btn-start {
  padding: 10px 24px;
  border: 1px solid #d5d5d5;
  border-radius: 8px;
  background: #fff;
  color: #333;
  font-size: 15px;
  cursor: pointer;
}
.btn-start:hover {
  background: #f5f5f5;
}
</style>
