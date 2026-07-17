<template>
  <div class="border-t border-[var(--border-light)] bg-white px-6 py-4">
    <div class="flex items-end gap-3 max-w-3xl mx-auto">
      <textarea
        v-model="text"
        class="flex-1 resize-none rounded-[var(--radius-md)] border border-[var(--border-light)] bg-[var(--bg-input)] px-4 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] outline-none transition duration-200 focus:border-[var(--border-focus)] focus:shadow-[var(--shadow-sm)]"
        rows="1"
        placeholder="输入消息..."
        @keydown.enter.exact.prevent="send"
      />
      <button
        class="flex-shrink-0 px-5 py-2.5 rounded-[var(--radius-sm)] text-sm font-semibold text-white transition duration-200"
        :class="text.trim()
          ? 'bg-[var(--accent)] hover:bg-[var(--accent-hover)] cursor-pointer'
          : 'bg-[var(--text-tertiary)] cursor-not-allowed'"
        :disabled="!text.trim()"
        @click="send"
      >
        发送
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const text = ref('')

function send(): void {
  if (!text.value.trim()) return
  text.value = ''
}
</script>
