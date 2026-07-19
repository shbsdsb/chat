<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <button class="btn-new-chat" @click="handleNewChat">+ 新建对话</button>
    </div>
    <div class="sidebar-list">
      <ConversationItem
        v-for="conv in chatStore.conversations"
        :key="conv.id"
        :conversation="conv"
        :active="conv.id === chatStore.activeConvId"
        @select="chatStore.selectConversation(conv.id)"
        @delete="chatStore.deleteConversation(conv.id)"
        @rename="(title) => chatStore.renameConversation(conv.id, title)"
      />
    </div>
  </aside>
</template>

<script setup>
import { useChatStore } from "@/stores/chat";
import ConversationItem from "@/components/ConversationItem.vue";

const chatStore = useChatStore();

function handleNewChat() {
  chatStore.createConversation();
}
</script>

<style scoped>
.sidebar {
  width: 260px;
  min-width: 260px;
  height: 100%;
  background: #f5f5f5;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e0e0e0;
}

.sidebar-header {
  padding: 12px;
}

.btn-new-chat {
  width: 100%;
  padding: 8px 16px;
  border: 1px solid #d5d5d5;
  border-radius: 8px;
  background: #fff;
  color: #333;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-new-chat:hover {
  background: #e8e8e8;
}

.sidebar-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 8px;
}
</style>
