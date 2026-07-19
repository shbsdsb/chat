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
import { ref } from "vue";
import { useChatStore } from "@/stores/chat";
import ConversationItem from "@/components/ConversationItem.vue";

defineProps({
  visible: { type: Boolean, default: false },
});
defineEmits(["close"]);

const chatStore = useChatStore();
const drawerWidth = ref(280);
const resizing = ref(false);

function handleNewChat() {
  chatStore.createConversation();
}

function startResize(e) {
  e.preventDefault();
  resizing.value = true;
  document.body.style.userSelect = "none";
  document.body.style.cursor = "col-resize";

  const startX = e.clientX;
  const startW = drawerWidth.value;

  function onMove(ev) {
    const delta = ev.clientX - startX;
    drawerWidth.value = Math.max(220, Math.min(500, startW + delta));
  }

  function onUp() {
    resizing.value = false;
    document.body.style.userSelect = "";
    document.body.style.cursor = "";
    document.removeEventListener("mousemove", onMove);
    document.removeEventListener("mouseup", onUp);
  }

  document.addEventListener("mousemove", onMove);
  document.addEventListener("mouseup", onUp);
}
</script>

<style scoped>
.drawer-panel {
  width: 0;
  overflow: hidden;
  display: flex;
  flex-shrink: 0;
  transition: width 0.25s ease;
  position: relative;
}
.drawer-panel.resizing {
  transition: none;
}

.drawer-inner {
  flex: 1;
  background: #f5f5f5;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}
.drawer-header h3 {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  white-space: nowrap;
}

.drawer-close {
  width: 28px;
  height: 28px;
  border: 1px solid #d5d5d5;
  border-radius: 6px;
  background: #fff;
  color: #888;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.drawer-close:hover {
  background: #f0f0f0;
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

.conv-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.drawer-resizer {
  width: 4px;
  cursor: col-resize;
  background: transparent;
  flex-shrink: 0;
  transition: background 0.15s;
  user-select: none;
}
.drawer-resizer:hover,
.drawer-resizer.active {
  background: #d0d0d0;
}
</style>
