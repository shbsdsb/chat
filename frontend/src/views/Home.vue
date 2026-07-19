<template>
  <div class="chat-view">
    <div class="chat-content">
      <MessageList />
      <InputBar />
    </div>
  </div>
</template>

<script setup>
import MessageList from "@/components/MessageList.vue";
import InputBar from "@/components/InputBar.vue";
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}
</style>
