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
    <button class="fetch-btn" @click="handleFetch" :disabled="fetching">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ spinning: fetching }"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.13-9.36L23 10"/></svg>
      拉取
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
.model-row { display: flex; gap: 6px; align-items: center; }

.model-select {
  flex: 1; padding: 7px 10px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  font-size: 13px; color: var(--text-primary);
  background: var(--bg-input); outline: none;
  font-family: inherit; cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.model-select:focus {
  border-color: var(--accent);
  box-shadow: var(--focus-ring);
}

.fetch-btn {
  height: 32px; padding: 0 10px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  background: var(--bg-input); color: var(--text-secondary);
  cursor: pointer; font-size: 12px;
  display: flex; align-items: center; gap: 5px;
  transition: all 0.15s; font-family: inherit;
}
.fetch-btn:hover:not(:disabled) {
  color: var(--text-primary);
  border-color: var(--border);
  background: var(--bg-input-hover);
}
.fetch-btn:disabled { opacity: 0.45; cursor: default; }

.spinning { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
