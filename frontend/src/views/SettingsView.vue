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
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { useSettingsStore } from "@/stores/settings";
import PresetSelector from "@/components/PresetSelector.vue";
import ModelSelector from "@/components/ModelSelector.vue";
import ResponseFormatInput from "@/components/ResponseFormatInput.vue";

const store = useSettingsStore();

onMounted(() => {
  store.loadPresets();
});
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
</style>
