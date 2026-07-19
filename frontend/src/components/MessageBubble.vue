<template>
  <div class="bubble-row" :class="message.role">
    <div class="bubble">
      <div
        v-if="message.role === 'assistant' && message.reasoning_content"
        class="reasoning-block"
      >
        <div class="reasoning-header" @click="reasoningOpen = !reasoningOpen">
          <span class="reasoning-icon">{{ reasoningOpen ? '▼' : '▶' }}</span>
          <span>思考过程</span>
        </div>
        <div v-show="reasoningOpen" class="reasoning-content">
          {{ message.reasoning_content }}
        </div>
      </div>
      <div
        v-if="message.role === 'assistant'"
        class="bubble-text"
        @click="onBubbleClick"
      >
        <div
          v-for="(html, index) in frozenHtmls"
          :key="index"
          v-html="html"
        />
        <div v-html="liveHtml" />
      </div>
      <div v-else class="bubble-text">{{ message.content }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useMarkdown } from "@/composables/useMarkdown.js";

const props = defineProps({
  message: { type: Object, required: true },
});

const reasoningOpen = ref(true);

const content = computed(() => props.message.content);
const { frozenHtmls, liveHtml } = useMarkdown(content);

function onBubbleClick(event) {
  const btn = event.target.closest('.copy-btn');
  if (!btn) return;

  const wrapper = btn.closest('.code-block-wrapper');
  const code = wrapper.querySelector('code').textContent;

  navigator.clipboard.writeText(code).then(() => {
    btn.querySelector('.copy-icon').style.display = 'none';
    btn.querySelector('.check-icon').style.display = '';
    setTimeout(() => {
      btn.querySelector('.copy-icon').style.display = '';
      btn.querySelector('.check-icon').style.display = 'none';
    }, 2000);
  });
}
</script>

<style scoped>
.bubble-row {
  display: flex;
  margin-bottom: 12px;
}
.bubble-row.user {
  justify-content: flex-end;
}
.bubble-row.assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: 70%;
  min-width: 0;
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid #e0e0e0;
  background: #fff;
  color: #333;
  font-size: 15px;
  line-height: 1.6;
  overflow: hidden;
}
.bubble-row.user .bubble {
  border-color: #d5d5d5;
}
.bubble-row.assistant .bubble {
  border-color: #e8e8e8;
}

.bubble-text {
  word-break: break-word;
  overflow: hidden;
}

/* ── 推理块 ──────────────────────────────────── */

.reasoning-block {
  margin-bottom: 10px;
  border-left: 2px solid #d0d0d0;
  padding-left: 10px;
}

.reasoning-header {
  cursor: pointer;
  font-size: 13px;
  color: #888;
  user-select: none;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 4px;
}

.reasoning-header:hover {
  color: #666;
}

.reasoning-icon {
  font-size: 10px;
  width: 12px;
}

.reasoning-content {
  font-size: 13px;
  color: #999;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
}

/* ── 代码块 ───────────────────────────────────── */

.bubble-text :deep(.code-block-wrapper) {
  position: relative;
  margin: 8px 0;
  max-width: 100%;
  overflow: auto;
}
.bubble-text :deep(.code-block-wrapper pre) {
  margin: 0;
  padding: 16px;
  border-radius: 6px;
  background: #f6f8fa;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.5;
}
.bubble-text :deep(.code-block-wrapper code) {
  background: transparent;
  padding: 0;
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
}

/* ── 复制按钮 ─────────────────────────────────── */

.bubble-text :deep(.copy-btn) {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 32px;
  height: 32px;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  background: #fff;
  color: #656d76;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.15s;
  padding: 0;
}
.bubble-text :deep(.code-block-wrapper:hover .copy-btn) {
  opacity: 1;
}
.bubble-text :deep(.copy-btn:hover) {
  background: #f3f4f6;
}

/* ── MD 通用元素 ──────────────────────────────── */

.bubble-text :deep(p) {
  margin: 0 0 8px;
}
.bubble-text :deep(p:last-child) {
  margin-bottom: 0;
}
.bubble-text :deep(ul),
.bubble-text :deep(ol) {
  padding-left: 20px;
  margin: 0 0 8px;
}
.bubble-text :deep(blockquote) {
  border-left: 3px solid #d0d7de;
  padding-left: 12px;
  margin: 8px 0;
  color: #656d76;
}
.bubble-text :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
  width: 100%;
}
.bubble-text :deep(th),
.bubble-text :deep(td) {
  border: 1px solid #d0d7de;
  padding: 6px 12px;
  text-align: left;
}
.bubble-text :deep(th) {
  background: #f6f8fa;
  font-weight: 600;
}
</style>
