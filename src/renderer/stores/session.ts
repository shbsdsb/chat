import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Session } from '@/types'

export const useSessionStore = defineStore('session', () => {
  const sessions = ref<Session[]>([])
  const currentId = ref<string | null>(null)

  const currentSession = computed(() =>
    sessions.value.find((s) => s.id === currentId.value) ?? null,
  )

  function createSession(): string {
    const id = crypto.randomUUID()
    const session: Session = {
      id,
      title: '新会话',
      createdAt: Date.now(),
    }
    sessions.value.unshift(session)
    currentId.value = id
    return id
  }

  function switchSession(id: string): void {
    if (sessions.value.some((s) => s.id === id)) {
      currentId.value = id
    }
  }

  function deleteSession(id: string): void {
    const idx = sessions.value.findIndex((s) => s.id === id)
    if (idx === -1) return

    sessions.value.splice(idx, 1)

    if (currentId.value === id) {
      if (sessions.value.length > 0) {
        currentId.value = sessions.value[Math.min(idx, sessions.value.length - 1)].id
      } else {
        currentId.value = null
      }
    }
  }

  return { sessions, currentId, currentSession, createSession, switchSession, deleteSession }
})
