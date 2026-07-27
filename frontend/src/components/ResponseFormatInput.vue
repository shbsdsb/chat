<template>
  <textarea
    v-model="store.responseFormat"
    class="resp-format-input"
  ></textarea>
</template>

<script setup>
import { useSettingsStore } from "@/stores/settings";
const store = useSettingsStore();
</script>

<style scoped>
.resp-format-input {
  width: 100%; min-height: 90px;
  padding: 10px 12px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  font-size: 12px; color: var(--text-primary);
  background: var(--bg-input); outline: none;
  resize: vertical; line-height: 1.5;
  font-family: "Consolas", "Monaco", monospace;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.resp-format-input:focus {
  border-color: var(--accent);
  box-shadow: var(--focus-ring);
}
.resp-format-input::placeholder { color: var(--text-muted); }
</style>
