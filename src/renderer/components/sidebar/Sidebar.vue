<template>
  <div
    class="w-sidebar flex-shrink-0 flex flex-col bg-[var(--bg-sidebar)] border-r border-[var(--border-light)]"
  >
    <div class="flex items-center justify-between h-12 px-4">
      <span class="text-lg font-semibold text-[var(--text-primary)]">会话</span>
      <button
        class="w-8 h-8 flex items-center justify-center rounded-[var(--radius-sm)] bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)] transition duration-150"
        @click="create"
      >
        <svg width="16" height="16" viewBox="0 0 16 16">
          <line x1="8" y1="2" x2="8" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <line x1="2" y1="8" x2="14" y2="8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </button>
    </div>
    <SessionList
      :sessions="store.sessions"
      :currentSessionId="store.currentSessionId"
      @select="store.switchSession"
      @delete="store.deleteSession"
    />
  </div>
</template>

<script setup lang="ts">
import { useSessionStore } from '@/stores/session'
import SessionList from './SessionList.vue'

const store = useSessionStore()

function create() {
  store.createSession()
}
</script>
