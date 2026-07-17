<template>
  <div class="flex-1 overflow-y-auto flex flex-col items-center justify-center p-6">
    <div class="text-center">
      <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-[var(--bg-hover)] flex items-center justify-center">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" stroke-width="1.5" stroke-linecap="round">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/>
          <circle cx="8" cy="10" r="1" fill="var(--text-tertiary)" stroke="none"/>
          <circle cx="16" cy="10" r="1" fill="var(--text-tertiary)" stroke="none"/>
          <path d="M8 15c1.5 2 4 2 8 0"/>
        </svg>
      </div>
      <h2 class="text-[24px] font-semibold text-[var(--text-primary)] mb-2">
        欢迎使用 AI Chat
      </h2>
      <p class="text-sm text-[var(--text-tertiary)]">
        选择一个会话或创建新会话开始对话
      </p>
    </div>
  </div>
</template>
