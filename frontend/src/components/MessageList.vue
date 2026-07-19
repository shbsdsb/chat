<template>
  <div class="message-list" ref="listRef">
    <template v-for="msg in chatStore.messages" :key="msg.id">
      <MessageBubble :message="msg" />
      <MessageActions
        v-if="isLastAssistant(msg)"
        :message="msg"
        @edit="handleEdit"
        @replay="handleReplay"
        @prev="(id) => chatStore.switchVersion(id, -1)"
        @next="(id) => chatStore.switchVersion(id, 1)"
      />
    </template>
    <div v-if="chatStore.messages.length === 0" class="empty-hint">
      发送一条消息开始对话
    </div>
  </div>
</template>

<script setup>
import { watch, nextTick, ref } from "vue";
import { useChatStore } from "@/stores/chat";
import MessageBubble from "@/components/MessageBubble.vue";
import MessageActions from "@/components/MessageActions.vue";

const chatStore = useChatStore();
const listRef = ref(null);

function isLastAssistant(msg) {
  const msgs = chatStore.messages;
  if (msg.role !== "assistant") return false;
  for (let i = msgs.length - 1; i >= 0; i--) {
    if (msgs[i].role === "assistant") return msgs[i].id === msg.id;
  }
  return false;
}

function handleEdit(id) {
  const msg = chatStore.messages.find((m) => m.id === id);
  if (!msg) return;
  const newContent = prompt("编辑消息", msg.content);
  if (newContent !== null && newContent.trim()) {
    chatStore.editMessage(id, newContent.trim());
  }
}

function handleReplay(id) {
  chatStore.replayMessage(id);
}

watch(
  () => chatStore.messages.length,
  () => nextTick(() => {
    if (listRef.value) {
      listRef.value.scrollTop = listRef.value.scrollHeight;
    }
  })
);
</script>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
}
.empty-hint {
  text-align: center;
  color: #999;
  margin-top: 40px;
  font-size: 14px;
}
</style>
