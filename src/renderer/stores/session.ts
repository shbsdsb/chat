import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Session } from '@/types'

export const useSessionStore = defineStore('session', () => {
  const sessions = ref<Session[]>([])
  const currentSessionId = ref<string | null>(null)

  const currentSession = computed(() =>
    sessions.value.find((s) => s.id === currentSessionId.value) ?? null,
  )

  function createSession(): string {
    const id = crypto.randomUUID()
    const session: Session = {
      id,
      title: '新会话',
      createdAt: Date.now(),
    }
    sessions.value.unshift(session)
    currentSessionId.value = id
    return id
  }

  function switchSession(id: string): void {
    if (sessions.value.some((s) => s.id === id)) {
      currentSessionId.value = id
    } else {
      console.warn(`[useSessionStore] switchSession: unknown session id "${id}"`)
    }
  }

  function deleteSession(id: string): void {
    const idx = sessions.value.findIndex((s) => s.id === id)
    if (idx === -1) return

    sessions.value.splice(idx, 1)

    if (currentSessionId.value === id) {
      if (sessions.value.length > 0) {
        currentSessionId.value = sessions.value[Math.min(idx, sessions.value.length - 1)].id
      } else {
        currentSessionId.value = null
      }
    }
  }

  return { sessions, currentSessionId, currentSession, createSession, switchSession, deleteSession }
})
