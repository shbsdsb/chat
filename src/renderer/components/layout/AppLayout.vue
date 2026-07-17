<template>
  <div class="w-screen h-screen flex flex-col bg-[var(--bg-app)]">
    <AppTitleBar />
    <div class="flex flex-1 overflow-hidden">
      <slot name="sidebar" />
      <slot name="chat" />
    </div>
  </div>
</template>

<script setup lang="ts">
import AppTitleBar from './AppTitleBar.vue'
</script>
