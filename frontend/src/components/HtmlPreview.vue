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
      <pre><code class="hljs language-html" v-html="highlightedHtml"></code></pre>
    </div>

    <!-- 预览视图 -->
    <div v-show="mode === 'preview'" class="preview-view">
      <iframe
        v-if="useBlob"
        ref="previewFrame"
        sandbox="allow-scripts"
        :src="blobUrl"
        class="preview-frame"
      />
      <iframe
        v-else
        ref="previewFrame"
        sandbox="allow-scripts"
        :srcdoc="srcdocWithScript"
        class="preview-frame"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import hljs from 'highlight.js';

const props = defineProps({
  code: { type: String, required: true },
});

const mode = ref('code');
const previewFrame = ref(null);
const frameHeight = ref('300px');

// ── postMessage 高度上报脚本（注入到 iframe 内）─

const HEIGHT_SCRIPT = '<script>(function(){function r(){parent.postMessage({t:"h",h:document.body.scrollHeight},"*")}new MutationObserver(r).observe(document.body,{childList:!0,subtree:!0,attributes:!0});addEventListener("load",r);if(document.readyState==="complete")r()})()<\/script>';

// ── Blob URL 生命周期管理 ───────────────────────

const blobUrl = ref(null);
const useBlob = computed(() => props.code && props.code.length > 100 * 1024);

function createBlobUrl(raw) {
  // 注入高度上报脚本后创建 blob
  const blob = new Blob([HEIGHT_SCRIPT + raw], { type: 'text/html' });
  return URL.createObjectURL(blob);
}

function revokeBlobUrl() {
  if (blobUrl.value) {
    URL.revokeObjectURL(blobUrl.value);
    blobUrl.value = null;
  }
}

// srcdoc 内容：注入高度上报脚本
const srcdocWithScript = computed(() => HEIGHT_SCRIPT + props.code);

// code 变化时管理 blob URL 生命周期
watch(() => props.code, (raw) => {
  revokeBlobUrl();
  if (raw && useBlob.value) {
    blobUrl.value = createBlobUrl(raw);
  }
}, { immediate: true });

// ── 代码高亮 ─────────────────────────────────────

const highlightedHtml = computed(() => {
  if (!props.code) return '';
  try {
    return hljs.highlight(props.code, { language: 'html' }).value;
  } catch {
    return hljs.escapeHtml ? hljs.escapeHtml(props.code) : props.code;
  }
});

// ── iframe 高度自适应（postMessage 方案）───────

function onHeightMessage(e) {
  if (e.data && e.data.t === 'h') {
    frameHeight.value = Math.max(e.data.h, 100) + 'px';
  }
}

onMounted(() => {
  window.addEventListener('message', onHeightMessage);
});

// ── 复制 ─────────────────────────────────────────

function onCopy(e) {
  const btn = e.currentTarget;
  const copyIcon = btn.querySelector('.copy-icon');
  const checkIcon = btn.querySelector('.check-icon');

  navigator.clipboard.writeText(props.code).then(() => {
    copyIcon.style.display = 'none';
    checkIcon.style.display = '';
    setTimeout(() => {
      copyIcon.style.display = '';
      checkIcon.style.display = 'none';
    }, 2000);
  }).catch(() => {});
}

// ── 清理 ─────────────────────────────────────────

onBeforeUnmount(() => {
  window.removeEventListener('message', onHeightMessage);
  revokeBlobUrl();
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
