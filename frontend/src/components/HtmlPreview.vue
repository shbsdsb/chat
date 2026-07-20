<template>
  <div class="html-preview-block">
    <div class="preview-toolbar">
      <button
        :class="{ active: mode === 'code' }"
        @click="mode = 'code'"
        title="查看代码"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
        <span>代码</span>
      </button>
      <button
        :class="{ active: mode === 'preview' }"
        @click="mode = 'preview'"
        title="预览效果"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
        <span>预览</span>
      </button>
      <button class="copy-btn" title="复制代码" @click="onCopy">
        <svg class="copy-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
        <svg class="check-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" style="display:none"><polyline points="20 6 9 17 4 12"/></svg>
      </button>
    </div>

    <!-- 代码视图 -->
    <div v-show="mode === 'code'" class="code-view">
      <pre><code class="hljs language-html" v-html="highlightedHtml" />
    </div>

    <!-- 预览视图 -->
    <div v-show="mode === 'preview'" class="preview-view">
      <iframe
        ref="previewFrame"
        sandbox="allow-scripts"
        :srcdoc="srcdocContent"
        class="preview-frame"
        @load="onFrameLoad"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue';
import hljs from 'highlight.js';

const props = defineProps({
  code: { type: String, required: true },
});

const mode = ref('code');
const previewFrame = ref(null);
const frameHeight = ref('300px');

// ── Blob URL 生命周期管理 ───────────────────────

const blobUrl = ref(null);

function createBlobUrl(raw) {
  const blob = new Blob([raw], { type: 'text/html' });
  return URL.createObjectURL(blob);
}

function revokeBlobUrl() {
  if (blobUrl.value) {
    URL.revokeObjectURL(blobUrl.value);
    blobUrl.value = null;
  }
}

// 超长 HTML (>100KB) 用 blob: URL 替代直接 srcdoc
const srcdocContent = computed(() => {
  const raw = props.code;
  if (raw.length > 100 * 1024) {
    revokeBlobUrl();               // 先释放旧 URL
    blobUrl.value = createBlobUrl(raw);
    return blobUrl.value;
  }
  return raw;
});

// props.code 变化时释放旧 blob URL（确保非超长→超长切换时也清理）
watch(() => props.code, () => {
  // srcdocContent 已处理超长情况；若切回短文本则清理残留
  if (props.code && props.code.length <= 100 * 1024) {
    revokeBlobUrl();
  }
});

// ── 代码高亮 ─────────────────────────────────────

const highlightedHtml = computed(() => {
  if (!props.code) return '';
  try {
    return hljs.highlight(props.code, { language: 'html' }).value;
  } catch {
    return hljs.escapeHtml ? hljs.escapeHtml(props.code) : props.code;
  }
});

// ── iframe 高度自适应 ────────────────────────────

let observer = null;

function updateFrameHeight() {
  try {
    const body = previewFrame.value?.contentDocument?.body;
    if (body) {
      frameHeight.value = Math.max(body.scrollHeight, 100) + 'px';
    }
  } catch {
    // 忽略跨域限制
  }
}

function onFrameLoad() {
  if (!previewFrame.value) return;

  // 清理旧的 observer
  if (observer) observer.disconnect();

  try {
    const body = previewFrame.value.contentDocument?.body;
    if (body) {
      updateFrameHeight();

      // MutationObserver 监听内容动态变化（JS 添加元素、展开折叠等）
      observer = new MutationObserver(() => {
        updateFrameHeight();
      });
      observer.observe(body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['style', 'class'],
      });
    }
  } catch {
    // 忽略
  }
}

// ── 复制 ─────────────────────────────────────────

function onCopy(e) {
  navigator.clipboard.writeText(props.code).then(() => {
    const btn = e.currentTarget;
    btn.querySelector('.copy-icon').style.display = 'none';
    btn.querySelector('.check-icon').style.display = '';
    setTimeout(() => {
      btn.querySelector('.copy-icon').style.display = '';
      btn.querySelector('.check-icon').style.display = 'none';
    }, 2000);
  });
}

// ── 清理 ─────────────────────────────────────────

onBeforeUnmount(() => {
  revokeBlobUrl();
  if (observer) observer.disconnect();
});
</script>

<style scoped>
.html-preview-block {
  margin: 8px 0;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  overflow: hidden;
}

.preview-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 8px;
  background: #f6f8fa;
  border-bottom: 1px solid #d0d7de;
}

.preview-toolbar button {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid transparent;
  border-radius: 4px;
  background: transparent;
  color: #656d76;
  cursor: pointer;
  font-size: 12px;
  line-height: 1;
}

.preview-toolbar button:hover {
  background: #eaeef2;
}

.preview-toolbar button.active {
  background: #fff;
  border-color: #d0d7de;
  color: #24292f;
}

.preview-toolbar .copy-btn {
  margin-left: auto;
}

.code-view pre {
  margin: 0;
  padding: 12px 16px;
  background: #f6f8fa;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.5;
}

.code-view code {
  background: transparent;
  padding: 0;
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
}

.preview-view {
  background: #fff;
}

.preview-frame {
  width: 100%;
  height: v-bind(frameHeight);
  border: none;
  display: block;
}
</style>
