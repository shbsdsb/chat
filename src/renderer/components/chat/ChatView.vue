<template>
  <div class="flex-1 flex flex-col bg-[var(--bg-chat)] min-w-0">
    <div
      v-if="store.currentSession"
      class="flex items-center h-12 px-6 border-b border-[var(--border-light)] flex-shrink-0"
    >
      <span class="text-[15px] font-medium text-[var(--text-primary)] truncate">
        {{ store.currentSession.title }}
      </span>
    </div>
    <MessageList />
    <InputArea />
  </div>
</template>

<script setup lang="ts">
import { useSessionStore } from '@/stores/session'
import MessageList from './MessageList.vue'
import InputArea from './InputArea.vue'

const store = useSessionStore()
</script>
