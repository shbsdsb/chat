<template>
    <div class="bubble-row" :class="[message.role, { entering: isEntering }]">
        <!-- 角色标签 -->
        <span class="bubble-role-label">{{ message.role === 'user' ? '你' : 'Chat' }}</span>

        <!-- 编辑工具栏 -->
        <div v-if="isEditing" class="edit-toolbar">
            <button class="edit-btn save-btn" title="保存" @click="handleSave">✓</button>
            <button class="edit-btn cancel-btn" title="取消" @click="handleCancel">✗</button>
        </div>

        <!-- 完整 HTML 文档 -->
        <div v-if="isCompleteHtml && blocks.length === 1" class="bubble bubble-html" style="width:100%;padding:0">
            <div v-if="message.role === 'assistant' && message.reasoning_content"
                 class="reasoning-block"
                 style="padding: 12px 16px 0;">
                <div class="reasoning-header" @click="reasoningOpen = !reasoningOpen">
                    <span class="reasoning-icon">{{ reasoningOpen ? '▼' : '▶' }}</span>
                    <span>思考过程</span>
                </div>
                <div v-show="reasoningOpen" class="reasoning-content">
                    {{ message.reasoning_content }}
                </div>
            </div>
            <HtmlPreview :code="blocks[0].code" :showToggle="false" />
        </div>

        <div v-else class="bubble" :class="{ 'bubble-editing': isEditing }">
            <!-- 编辑模式：原始文本输入框 -->
            <textarea v-if="isEditing"
                      ref="editTextareaRef"
                      v-model="editContent"
                      class="edit-textarea"
                      rows="6" />
            <!-- 正常显示模式 -->
            <template v-else>
                <div v-if="message.role === 'assistant' && message.reasoning_content"
                     class="reasoning-block">
                    <div class="reasoning-header" @click="reasoningOpen = !reasoningOpen">
                        <span class="reasoning-icon">{{ reasoningOpen ? '▼' : '▶' }}</span>
                        <span>思考过程</span>
                    </div>
                    <div v-show="reasoningOpen" class="reasoning-content">
                        {{ message.reasoning_content }}
                    </div>
                </div>

                <!-- 混合 blocks 渲染 -->
                <template v-if="blocks.length > 0">
                    <div @click="onBubbleClick">
                        <template v-for="(block, i) in blocks" :key="i">
                            <div v-if="block.type === 'text'" v-html="block.html" class="bubble-text" />
                            <div v-else class="html-auto-block">
                                <HtmlPreview :code="block.code" :showToggle="false" />
                            </div>
                        </template>
                        <div v-if="liveHtml" v-html="liveHtml" class="bubble-text" />
                    </div>
                </template>

                <!-- 纯文本：现有渲染 -->
                <template v-else>
                    <div v-if="message.role === 'assistant'"
                         ref="bubbleTextRef"
                         class="bubble-text"
                         @click="onBubbleClick">
                        <div v-for="(html, index) in frozenHtmls"
                             :key="index"
                             v-html="html" />
                        <div v-html="liveHtml" />
                    </div>
                    <div v-else class="bubble-text">{{ message.content }}</div>
                </template>
            </template>

            <!-- 扩展：message_decorator 插槽 -->
            <ExtensionSlot name="message_decorator" :message="message" :conversation="chatStore.activeConversation" />
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick, createApp } from "vue";
import { useMarkdown } from "@/composables/useMarkdown.js";
import { useChatStore } from "@/stores/chat";
import HtmlPreview from "@/components/HtmlPreview.vue";
import ExtensionSlot from "@/extensions/ExtensionSlot.vue";

const props = defineProps({
  message: { type: Object, required: true },
});

const chatStore = useChatStore();
const reasoningOpen = ref(true);

const content = computed(() => props.message.content);
const { frozenHtmls, liveHtml, blocks, isCompleteHtml } = useMarkdown(content);

// ── 编辑模式 ─────────────────────────────────

const isEditing = computed(() => chatStore.editingMessageId === props.message.id);
const editContent = ref("");
const editTextareaRef = ref(null);

watch(isEditing, (val) => {
  if (val) {
    editContent.value = props.message.content;
    nextTick(() => {
      const ta = editTextareaRef.value;
      if (ta) {
        ta.style.height = "auto";
        ta.style.height = ta.scrollHeight + "px";
        ta.focus();
      }
    });
  }
});

function handleSave() {
  const trimmed = editContent.value.trim();
  if (!trimmed) return;
  chatStore.editMessage(props.message.id, trimmed);
}

function handleCancel() {
  chatStore.exitEditMode();
}

// ── HtmlPreview 增量挂载 ────────────────────────

const bubbleTextRef = ref(null);
const previewApps = new Map();  // DOM element → Vue app

function mountHtmlPreviews() {
  if (!bubbleTextRef.value) return;

  const containers = bubbleTextRef.value.querySelectorAll('.html-preview-container');
  const currentContainers = new Set(containers);

  // 增量挂载：仅处理尚未挂载的新容器
  containers.forEach(container => {
    if (previewApps.has(container)) return;  // 已挂载，跳过

    const base64 = container.getAttribute('data-html-code');
    if (!base64) return;

    let code;
    try {
      const bytes = Uint8Array.from(atob(base64), c => c.charCodeAt(0));
      code = new TextDecoder().decode(bytes);
    } catch {
      code = '';
    }

    const app = createApp(HtmlPreview, { code });
    app.mount(container);
    previewApps.set(container, app);
  });

  // 清理已从 DOM 中移除的容器（消息重新生成、段落减少等场景）
  previewApps.forEach((app, container) => {
    if (!currentContainers.has(container) || !document.contains(container)) {
      app.unmount();
      previewApps.delete(container);
    }
  });
}

function unmountHtmlPreviews() {
  previewApps.forEach((app) => app.unmount());
  previewApps.clear();
}

// 增量挂载：不全量卸载，仅处理新增/移除的容器
watch([frozenHtmls, liveHtml], () => {
  nextTick(() => mountHtmlPreviews());
});

onMounted(() => {
  nextTick(() => mountHtmlPreviews());
});

onBeforeUnmount(() => {
  unmountHtmlPreviews();
});

// ── 事件委托：仅处理非 HTML 代码块的复制 ─────────

function onBubbleClick(event) {
  const btn = event.target.closest('.copy-btn');
  if (!btn) return;

  // 跳过 HtmlPreview 内部的复制按钮（组件自管理）
  if (btn.closest('.html-preview-block')) return;

  const wrapper = btn.closest('.code-block-wrapper');
  if (!wrapper) return;

  const code = wrapper.querySelector('code')?.textContent || '';

  navigator.clipboard.writeText(code).then(() => {
    btn.querySelector('.copy-icon').style.display = 'none';
    btn.querySelector('.check-icon').style.display = '';
    setTimeout(() => {
      btn.querySelector('.copy-icon').style.display = '';
      btn.querySelector('.check-icon').style.display = 'none';
    }, 2000);
  }).catch(() => {});
}
</script>

<style scoped>
/* ── 气泡行 ──────────────────────────────── */
.bubble-row {
  display: flex;
  flex-direction: column;
  margin-bottom: 16px;
  padding: 0 8px;
}
.bubble-row.user {
  align-items: flex-end;
}
.bubble-row.assistant {
  align-items: flex-start;
}

/* ── 角色标签 ────────────────────────────── */
.bubble-role-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
  padding: 0 4px;
  user-select: none;
}

/* ── 入场动画 ────────────────────────────── */
.bubble-row.entering .bubble {
  animation: message-enter 0.25s ease-out;
}

/* ── 气泡容器 ────────────────────────────── */
.bubble {
  max-width: 70%;
  min-width: 0;
  padding: 12px 16px;
  font-size: 15px;
  line-height: 1.6;
  overflow: hidden;
}

/* ── User 气泡：靛蓝渐变 ─────────────────── */
.bubble-row.user .bubble {
  background: linear-gradient(135deg, var(--accent), var(--accent-light));
  color: #fff;
  border-radius: var(--radius-lg) 4px var(--radius-lg) var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

/* ── Assistant 气泡：灰底 ────────────────── */
.bubble-row.assistant .bubble {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border-radius: 4px var(--radius-lg) var(--radius-lg) var(--radius-lg);
  box-shadow: var(--shadow-xs);
}

/* ── 编辑模式 ────────────────────────────── */
.bubble-editing {
  width: 100%;
  padding: 0;
  border: 1.5px solid var(--accent);
  box-shadow: var(--shadow-md);
  transition: border 0.2s ease, box-shadow 0.2s ease;
}

.edit-toolbar {
  display: flex;
  gap: 6px;
  margin-bottom: 6px;
}

.edit-btn {
  width: 30px;
  height: 30px;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  font-size: 15px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.save-btn {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}
.save-btn:hover {
  background: #3d5ce5;
  border-color: #3d5ce5;
}

.cancel-btn {
  background: #fff;
  color: var(--text-muted);
}
.cancel-btn:hover {
  background: #f0f1f5;
  color: var(--text-secondary);
}

.edit-textarea {
  width: 100%;
  min-width: 420px;
  min-height: 120px;
  padding: 16px;
  border: none;
  border-radius: 12px;
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  background: #fafbfc;
  resize: vertical;
  outline: none;
  box-sizing: border-box;
}

.bubble-text {
  word-break: break-word;
  overflow: hidden;
}

/* ── 推理块 ──────────────────────────────── */
.reasoning-block {
  margin-bottom: 10px;
  border-left: 3px solid var(--accent);
  padding-left: 10px;
}

.reasoning-header {
  cursor: pointer;
  font-size: 13px;
  color: var(--text-muted);
  user-select: none;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 4px;
}
.reasoning-header:hover {
  color: var(--text-secondary);
}

.reasoning-icon {
  font-size: 10px;
  width: 12px;
  transition: transform 0.2s ease;
}

.reasoning-content {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
  transition: max-height 0.3s ease;
}
.reasoning-block:not(.is-open) .reasoning-content {
  max-height: 0;
  overflow: hidden;
}

/* ── 代码块 ──────────────────────────────── */
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

/* ── 复制按钮 ────────────────────────────── */
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

/* ── MD 通用元素 ──────────────────────────── */
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

/* ── HtmlPreview ──────────────────────────── */
.bubble-text :deep(.html-preview-container) {
  margin: 8px 0;
}
.html-auto-block {
  margin: 8px 0;
}
</style>
