import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { AppState } from '@/types'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref<AppState['sidebarCollapsed']>(false)
  const theme = ref<AppState['theme']>('light')

  function toggleSidebar(): void {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setTheme(t: 'dark' | 'light'): void {
    theme.value = t
    document.documentElement.classList.toggle('dark', t === 'dark')
  }

  return { sidebarCollapsed, theme, toggleSidebar, setTheme }
})
