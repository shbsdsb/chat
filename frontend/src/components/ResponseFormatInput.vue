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
  width: 100%;
  height: 150px;
  padding: 12px;
  border: 1px solid #d5d5d5;
  border-radius: 8px;
  font-size: 13px;
  font-family: "SF Mono", "Fira Code", "Consolas", monospace;
  color: #333;
  outline: none;
  resize: vertical;
  line-height: 1.5;
}
.resp-format-input:focus {
  border-color: #aaa;
}
.resp-format-input::placeholder {
  color: #bbb;
}
</style>
