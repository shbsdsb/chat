<template>
  <div class="model-row">
    <select v-model="store.model" class="model-select">
      <option v-for="m in store.availableModels" :key="m" :value="m">
        {{ m }}
      </option>
      <option v-if="store.availableModels.length === 0" :value="store.model">
        {{ store.model || 'gpt-4o' }}
      </option>
    </select>
    <button class="fetch-btn" title="拉取模型列表" @click="handleFetch" :disabled="fetching">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ spinning: fetching }"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.13-9.36L23 10"/></svg>
    </button>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useSettingsStore } from "@/stores/settings";
import { useAlertStore } from "@/stores/alert";
const store = useSettingsStore();
const alert = useAlertStore();
const fetching = ref(false);

async function handleFetch() {
  fetching.value = true;
  try {
    await store.fetchModels();
  } catch (e) {
    alert.error("拉取失败", e.message || "未知错误");
  } finally {
    fetching.value = false;
  }
}
</script>

<style scoped>
.model-row {
  display: flex;
  gap: 6px;
  align-items: center;
}

.model-select {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d5d5d5;
  border-radius: 8px;
  font-size: 14px;
  color: #333;
  background: #fff;
  outline: none;
  font-family: inherit;
}

.fetch-btn {
  width: 32px;
  height: 32px;
  border: 1px solid #d5d5d5;
  border-radius: 6px;
  background: #fff;
  color: #666;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.fetch-btn:hover:not(:disabled) {
  background: #f0f0f0;
  color: #333;
}
.fetch-btn:disabled {
  opacity: 0.3;
  cursor: default;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
