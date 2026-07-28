<template>
  <div class="input-bar">
    <div class="input-toolbar">
      <button class="model-badge" @click="$emit('open-model-selector')" title="切换模型">
        {{ currentModel }}
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
      </button>
    </div>
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
import { ref, computed } from "vue";
import { useChatStore } from "@/stores/chat";
import { useSettingsStore } from "@/stores/settings";

const chatStore = useChatStore();
const settingsStore = useSettingsStore();
const input = ref("");

const currentModel = computed(() => {
  const preset = settingsStore.presets?.find(p => p.id === settingsStore.activePresetId);
  return preset?.model || "选择模型";
});

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

<style>
.input-bar {
  padding: 8px 24px 16px;
  border-top: 1px solid transparent;
}

.input-toolbar {
  display: flex;
  align-items: center;
  padding: 0 4px 6px;
  min-height: 28px;
}

.model-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.model-badge:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: rgba(79,110,246,0.04);
}

.input-bar .input-wrapper {
  display: flex;
  align-items: center;
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  padding: 6px 6px 6px 18px;
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  box-shadow: var(--shadow-sm);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.input-bar .input-wrapper:focus-within {
  border-color: var(--accent);
  box-shadow: var(--shadow-sm), 0 0 0 3px rgba(79,110,246,0.1);
}

.input-bar .input-field {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: 15px;
  line-height: 1.5;
  max-height: 120px;
  padding: 4px 0;
  font-family: inherit;
  background: transparent;
  color: var(--text-primary);
}
.input-bar .input-field::placeholder {
  color: var(--text-muted);
}

.input-bar .btn-send {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: none;
  background: var(--accent);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.2s, transform 0.15s, box-shadow 0.15s;
  position: relative;
  overflow: hidden;
}
.input-bar .btn-send:hover {
  background: var(--accent-light);
  transform: scale(1.08);
  box-shadow: 0 0 16px rgba(79,110,246,0.35);
}
.input-bar .btn-send:active {
  transform: scale(0.92);
}
.input-bar .btn-send.is-streaming {
  background: var(--danger);
  animation: stop-pulse 1.2s ease-in-out infinite;
}
.input-bar .btn-send.is-streaming:hover {
  background: #dc2626;
  box-shadow: none;
}

.input-bar .icon-send {
  width: 18px;
  height: 18px;
  margin-left: 1px;
}

.input-bar .icon-stop {
  width: 14px;
  height: 14px;
}
</style>
