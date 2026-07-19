<template>
  <div
    class="conv-item"
    :class="{ active }"
    @click="$emit('select')"
  >
    <span class="conv-title">{{ conversation.title }}</span>
    <div class="conv-actions">
      <button class="conv-action-btn" title="编辑名称" @click.stop="startRename">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
      </button>
      <button class="conv-action-btn conv-action-delete" title="删除" @click.stop="startDelete">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
      </button>
    </div>

    <!-- 重命名弹窗 -->
    <Teleport to="body">
      <div v-if="showRename" class="dialog-overlay" @click.self="cancelRename">
        <div class="dialog-box">
          <div class="dialog-title">重命名</div>
          <input
            ref="nameInput"
            v-model="newName"
            class="dialog-input"
            placeholder="输入新名称"
            @keydown.enter="confirmRename"
            @keydown.escape="cancelRename"
          />
          <div class="dialog-actions">
            <button class="dialog-btn dialog-btn-cancel" @click="cancelRename">取消</button>
            <button class="dialog-btn dialog-btn-ok" @click="confirmRename" :disabled="!newName.trim()">确定</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 删除确认弹窗 -->
    <Teleport to="body">
      <div v-if="showDelete" class="dialog-overlay" @click.self="cancelDelete">
        <div class="dialog-box dialog-danger">
          <div class="dialog-danger-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#ef5350" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          </div>
          <p class="dialog-danger-msg">确定要删除对话「{{ conversation.title }}」吗？此操作不可撤销。</p>
          <div class="dialog-actions">
            <button class="dialog-btn dialog-btn-cancel" @click="cancelDelete">取消</button>
            <button class="dialog-btn dialog-btn-danger" @click="confirmDelete">确定删除</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, nextTick } from "vue";
import { useChatStore } from "@/stores/chat";

const props = defineProps({
  conversation: { type: Object, required: true },
  active: { type: Boolean, default: false },
});

const emit = defineEmits(["select"]);

const chatStore = useChatStore();

// ── 重命名 ──────────────────────────────────────
const showRename = ref(false);
const newName = ref("");
const nameInput = ref(null);

async function startRename() {
  newName.value = props.conversation.title;
  showRename.value = true;
  await nextTick();
  nameInput.value?.focus();
  nameInput.value?.select();
}

async function confirmRename() {
  const name = newName.value.trim();
  if (!name) return;
  showRename.value = false;
  await chatStore.renameConversation(props.conversation.id, name);
}

function cancelRename() {
  showRename.value = false;
}

// ── 删除 ────────────────────────────────────────
const showDelete = ref(false);

function startDelete() {
  showDelete.value = true;
}

async function confirmDelete() {
  showDelete.value = false;
  await chatStore.deleteConversation(props.conversation.id);
}

function cancelDelete() {
  showDelete.value = false;
}
</script>

<style scoped>
.conv-item {
  padding: 8px 10px 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
}
.conv-item:hover {
  background: #e8e8e8;
}
.conv-item.active {
  background: #fff;
  border: 1px solid #d5d5d5;
}

.conv-title {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conv-actions {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
  visibility: hidden;
}
.conv-item:hover .conv-actions,
.conv-item.active .conv-actions {
  visibility: visible;
}

.conv-action-btn {
  width: 26px;
  height: 26px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: #999;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.12s, color 0.12s;
}
.conv-action-btn:hover {
  background: #ddd;
  color: #555;
}
.conv-action-delete:hover {
  background: #fdd;
  color: #d32f2f;
}

/* ── 弹窗 ─────────────────────────────────────── */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-box {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  width: 360px;
  max-width: 90vw;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.18);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dialog-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.dialog-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d5d5d5;
  border-radius: 8px;
  font-size: 14px;
  color: #333;
  outline: none;
  font-family: inherit;
  box-sizing: border-box;
}
.dialog-input:focus {
  border-color: #4a90d9;
  box-shadow: 0 0 0 2px rgba(74, 144, 217, 0.15);
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.dialog-btn {
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid transparent;
  transition: background 0.15s, color 0.15s;
  font-family: inherit;
}

.dialog-btn-cancel {
  background: #f5f5f5;
  color: #666;
  border-color: #ddd;
}
.dialog-btn-cancel:hover {
  background: #e8e8e8;
  color: #333;
}

.dialog-btn-ok {
  background: #4a90d9;
  color: #fff;
}
.dialog-btn-ok:hover:not(:disabled) {
  background: #357abd;
}
.dialog-btn-ok:disabled {
  opacity: 0.4;
  cursor: default;
}

.dialog-btn-danger {
  background: #ef5350;
  color: #fff;
}
.dialog-btn-danger:hover {
  background: #d32f2f;
}

.dialog-danger {
  width: 360px;
  text-align: center;
  border-top: 3px solid #ef5350;
}

.dialog-danger-icon {
  display: flex;
  justify-content: center;
}

.dialog-danger-msg {
  font-size: 14px;
  color: #555;
  line-height: 1.6;
  margin: 0;
}
</style>
