<template>
  <div class="settings-page">
    <div class="settings-section">
      <label class="section-label">预设</label>
      <PresetSelector />
    </div>

    <div class="settings-section">
      <label class="section-label">API URL</label>
      <input
        v-model="store.apiUrl"
        class="input-text"
        placeholder="https://api.openai.com/v1"
      />
    </div>

    <div class="settings-section">
      <label class="section-label">API Key</label>
      <input
        v-model="store.apiKey"
        class="input-text"
        type="password"
        placeholder="sk-..."
      />
    </div>

    <div class="settings-section">
      <label class="section-label">Model</label>
      <ModelSelector />
    </div>

    <div class="settings-section">
      <label class="section-label">response_format</label>
      <ResponseFormatInput />
    </div>

    <button
      class="test-btn"
      :disabled="testing || !store.apiUrl || !store.apiKey"
      @click="handleTestConnection"
    >
      <span v-if="testing" class="spinner"></span>
      {{ testing ? '测试中...' : '测试连接' }}
    </button>
    <p v-if="testResult" :class="['test-result', testOk ? 'ok' : 'fail']">
      {{ testResult }}
    </p>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useSettingsStore } from "@/stores/settings";
import PresetSelector from "@/components/PresetSelector.vue";
import ModelSelector from "@/components/ModelSelector.vue";
import ResponseFormatInput from "@/components/ResponseFormatInput.vue";

const store = useSettingsStore();
const testing = ref(false);
const testResult = ref("");
const testOk = ref(false);

onMounted(async () => {
  try {
    await store.loadPresets();
  } catch (e) {
    console.error("加载预设失败:", e);
  }
});

async function handleTestConnection() {
  testing.value = true;
  testResult.value = "";
  try {
    await store.fetchModels();
    testOk.value = true;
    testResult.value = `连接成功！获取到 ${store.availableModels.length} 个模型。`;
  } catch (e) {
    testOk.value = false;
    testResult.value = e?.response?.data?.detail || e?.message || "连接失败，请检查 API URL 和 Key。";
  } finally {
    testing.value = false;
  }
}
</script>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.settings-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.section-label {
  font-size: 13px;
  font-weight: 500;
  color: #888;
}

.input-text {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d5d5d5;
  border-radius: 8px;
  font-size: 14px;
  color: #333;
  outline: none;
  font-family: inherit;
}
.input-text:focus {
  border-color: #aaa;
}
.input-text::placeholder {
  color: #bbb;
}

.test-btn {
  width: 100%;
  padding: 10px 16px;
  border: 1px solid #4a90d9;
  border-radius: 8px;
  background: #4a90d9;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: background 0.15s;
  font-family: inherit;
}
.test-btn:hover:not(:disabled) {
  background: #357abd;
}
.test-btn:disabled {
  opacity: 0.5;
  cursor: default;
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

.test-result {
  margin-top: 4px;
  font-size: 13px;
  line-height: 1.4;
}
.test-result.ok {
  color: #2e7d32;
}
.test-result.fail {
  color: #c62828;
}
</style>
