<template>
  <div class="preset-row">
    <select v-model="store.activePresetId" class="preset-select" @change="onSelect">
      <option v-for="p in store.presets" :key="p.id" :value="p.id">
        {{ p.name }}
      </option>
    </select>
    <button class="preset-btn" title="保存" @click="handleSave" :disabled="!store.activePresetId">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
    </button>
    <button class="preset-btn" title="新建" @click="handleNew">+</button>
    <button class="preset-btn" title="删除" @click="handleDelete" :disabled="!store.activePresetId">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
    </button>
  </div>
</template>

<script setup>
import { useSettingsStore } from "@/stores/settings";
const store = useSettingsStore();

function onSelect() {
  store.selectPreset(store.activePresetId);
}

async function handleNew() {
  const name = prompt("预设名称");
  if (name && name.trim()) {
    await store.createPreset(name.trim());
  }
}

async function handleDelete() {
  if (confirm("确认删除当前预设？")) {
    await store.deletePreset(store.activePresetId);
  }
}

async function handleSave() {
  await store.savePreset();
  alert("保存成功");
}
</script>

<style scoped>
.preset-row {
  display: flex;
  gap: 6px;
  align-items: center;
}

.preset-select {
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

.preset-btn {
  width: 32px;
  height: 32px;
  border: 1px solid #d5d5d5;
  border-radius: 6px;
  background: #fff;
  color: #666;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  line-height: 1;
}
.preset-btn:hover:not(:disabled) {
  background: #f0f0f0;
  color: #333;
}
.preset-btn:disabled {
  opacity: 0.3;
  cursor: default;
}
</style>
