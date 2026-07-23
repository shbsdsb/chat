<template>
  <Teleport to="body">
    <div v-if="visible" class="dialog-overlay" @click.self="$emit('close')">
      <div class="dialog-box">
        <div v-if="title.trim()" class="dialog-title">{{ title }}</div>
        <div class="dialog-body">
          <slot />
        </div>
        <div v-if="$slots.footer" class="dialog-actions">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  title: { type: String, default: '' },
});

defineEmits(['close']);
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-box {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  width: 360px;
  max-width: 90vw;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.18);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dialog-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.dialog-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dialog-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
}

/* 全局输入框样式（:deep 穿透 scoped，供插槽内容复用） */
:deep(.dialog-input) {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d5d5d5;
  border-radius: 8px;
  font-size: 14px;
  color: #333;
  outline: none;
  font-family: inherit;
  box-sizing: border-box;
}
:deep(.dialog-input:focus) {
  border-color: #4a90d9;
  box-shadow: 0 0 0 2px rgba(74, 144, 217, 0.15);
}

/* 全局按钮样式 */
:deep(.dialog-btn) {
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid transparent;
  transition: background 0.15s, color 0.15s;
  font-family: inherit;
}

:deep(.dialog-btn-cancel) {
  background: #f5f5f5;
  color: #666;
  border-color: #ddd;
}
:deep(.dialog-btn-cancel:hover) {
  background: #e8e8e8;
  color: #333;
}

:deep(.dialog-btn-ok) {
  background: #4a90d9;
  color: #fff;
}
:deep(.dialog-btn-ok:hover:not(:disabled)) {
  background: #357abd;
}
:deep(.dialog-btn-ok:disabled) {
  opacity: 0.4;
  cursor: default;
}

:deep(.dialog-btn-danger) {
  background: #ef5350;
  color: #fff;
}
:deep(.dialog-btn-danger:hover) {
  background: #d32f2f;
}

/* 危险弹窗样式 */
:deep(.dialog-danger) {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  text-align: center;
}

:deep(.dialog-danger-icon) {
  display: flex;
  justify-content: center;
}

:deep(.dialog-danger-msg) {
  font-size: 14px;
  color: #555;
  line-height: 1.6;
  margin: 0;
  word-break: break-word;
  overflow-wrap: break-word;
}
</style>
