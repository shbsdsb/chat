<template>
  <div
    class="group flex items-center h-[56px] px-4 mx-2 rounded-[var(--radius-md)] cursor-pointer transition duration-200 select-none"
    :class="isActive
      ? 'bg-[var(--bg-active)] text-[var(--text-inverse)]'
      : 'hover:bg-[var(--bg-hover)] text-[var(--text-primary)]'"
    @click="$emit('select')"
  >
    <div class="flex-1 min-w-0">
      <p class="text-[15px] font-medium truncate">{{ session.title }}</p>
      <p
        class="text-xs mt-0.5"
        :class="isActive ? 'text-white/70' : 'text-[var(--text-tertiary)]'"
      >
        {{ formatTime(session.createdAt) }}
      </p>
    </div>
    <button
      class="ml-2 p-1 rounded-[var(--radius-sm)] opacity-0 group-hover:opacity-100 transition duration-150"
      :class="isActive
        ? 'hover:bg-white/20 text-white/80'
        : 'hover:bg-[var(--danger)] text-[var(--text-tertiary)] hover:text-white'"
      @click.stop="$emit('delete')"
    >
      <svg width="14" height="14" viewBox="0 0 14 14">
        <line x1="3" y1="3" x2="11" y2="11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        <line x1="11" y1="3" x2="3" y2="11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import type { Session } from '@/types'

defineProps<{
  session: Session
  isActive: boolean
}>()

defineEmits<{
  select: []
  delete: []
}>()

function formatTime(ts: number): string {
  const d = new Date(ts)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  if (isToday) {
    return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>
