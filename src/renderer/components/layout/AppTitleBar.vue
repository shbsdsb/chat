<template>
  <div
    class="app-titlebar flex items-center justify-between h-titlebar bg-[var(--bg-app)] border-b border-[var(--border-light)]"
    style="-webkit-app-region: drag"
  >
    <span class="pl-4 text-sm font-medium text-[var(--text-secondary)] select-none">
      AI Chat
    </span>
    <div class="flex h-full" style="-webkit-app-region: no-drag">
      <button
        class="w-[46px] h-full flex items-center justify-center text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] transition-fast"
        @click="minimize"
      >
        <svg width="12" height="12" viewBox="0 0 12 12"><rect y="5" width="12" height="1.5" fill="currentColor"/></svg>
      </button>
      <button
        class="w-[46px] h-full flex items-center justify-center text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] transition-fast"
        @click="maximize"
      >
        <svg width="12" height="12" viewBox="0 0 12 12"><rect x="1" y="1" width="10" height="10" stroke="currentColor" stroke-width="1.5" fill="none"/></svg>
      </button>
      <button
        class="w-[46px] h-full flex items-center justify-center text-[var(--text-secondary)] hover:bg-[var(--danger)] hover:text-white transition-fast"
        @click="close"
      >
        <svg width="12" height="12" viewBox="0 0 12 12"><line x1="1" y1="1" x2="11" y2="11" stroke="currentColor" stroke-width="1.5"/><line x1="11" y1="1" x2="1" y2="11" stroke="currentColor" stroke-width="1.5"/></svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
const api = window.electronAPI

function minimize() { api?.minimize() }
function maximize() { api?.maximize() }
function close() { api?.close() }
</script>
