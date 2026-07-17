<template>
  <div class="flex-1 overflow-y-auto py-1">
    <SessionItem
      v-for="session in sessions"
      :key="session.id"
      :session="session"
      :isActive="session.id === currentSessionId"
      @select="$emit('select', session.id)"
      @delete="$emit('delete', session.id)"
    />
    <div
      v-if="sessions.length === 0"
      class="px-4 py-8 text-center text-sm text-[var(--text-tertiary)]"
    >
      暂无会话
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Session } from '@/types'
import SessionItem from './SessionItem.vue'

defineProps<{
  sessions: Session[]
  currentSessionId: string | null
}>()

defineEmits<{
  select: [id: string]
  delete: [id: string]
}>()
</script>
