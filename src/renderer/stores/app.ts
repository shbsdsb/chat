import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const theme = ref<'dark' | 'light'>('light')

  function toggleSidebar(): void {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setTheme(t: 'dark' | 'light'): void {
    theme.value = t
    document.documentElement.classList.toggle('dark', t === 'dark')
  }

  return { sidebarCollapsed, theme, toggleSidebar, setTheme }
})
