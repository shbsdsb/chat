<template>
  <div class="chat-view">
    <WelcomeBanner v-if="!chatStore.activeConvId" />
    <div v-else class="chat-content">
      <MessageList />
      <InputBar />
    </div>
  </div>
</template>

<script setup>
import { useChatStore } from "@/stores/chat";
import WelcomeBanner from "@/components/WelcomeBanner.vue";
import MessageList from "@/components/MessageList.vue";
import InputBar from "@/components/InputBar.vue";

const chatStore = useChatStore();
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
