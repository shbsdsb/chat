export interface Session {
  id: string
  title: string
  createdAt: number
}

export interface AppState {
  sidebarCollapsed: boolean
  currentSessionId: string | null
  theme: 'dark' | 'light'
}
