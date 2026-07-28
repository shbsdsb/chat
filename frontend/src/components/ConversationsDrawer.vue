<template>
  <div
    class="drawer-panel"
    :class="{ open: visible, resizing: resizing }"
    :style="{ width: visible ? drawerWidth + 'px' : '0' }"
  >
    <div class="drawer-inner">
      <div class="drawer-header">
        <h3>会话记录</h3>
        <button class="drawer-close" @click="$emit('close')">✕</button>
      </div>
      <div class="drawer-body">
        <button class="btn-new-chat" @click="handleNewChat">+ 新建对话</button>
        <div class="conv-list">
          <ConversationItem
            v-for="conv in chatStore.conversations"
            :key="conv.id"
            :conversation="conv"
            :active="conv.id === chatStore.activeConvId"
            @select="chatStore.selectConversation(conv.id)"
          />
        </div>
      </div>
    </div>
    <div
      class="drawer-resizer"
      @mousedown="startResize"
      :class="{ active: resizing }"
    ></div>
  </div>
</template>

<script setup>
import { useResizableDrawer } from "@/composables/useResizableDrawer";
import { useChatStore } from "@/stores/chat";
import ConversationItem from "@/components/ConversationItem.vue";

defineProps({
  visible: { type: Boolean, default: false },
});
defineEmits(["close"]);

const chatStore = useChatStore();
const { width: drawerWidth, isResizing: resizing, startResize } = useResizableDrawer({
  direction: "left",
  minWidth: 220,
  maxWidth: 500,
  defaultWidth: 280,
});

function handleNewChat() {
  chatStore.createConversation();
}
</script>

<style>
@import "@/assets/drawer.css";
</style>

<style scoped>

.drawer-inner {
  flex: 1;
  background: var(--bg-tertiary);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.drawer-header h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.btn-new-chat {
  width: 100%;
  padding: 8px 16px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-new-chat:hover {
  background: var(--bg-input-hover);
}

.conv-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
</style>
