<template>
  <div
    class="drawer-panel"
    :class="{ open: visible, resizing: resizing }"
    :style="{ width: visible ? drawerWidth + 'px' : '0' }"
  >
    <div
      class="drawer-resizer"
      @mousedown="startResize"
      :class="{ active: resizing }"
    ></div>
    <div class="drawer-inner">
      <div class="drawer-header">
        <h3><slot name="title">设置</slot></h3>
        <button class="drawer-close" @click="$emit('close')">✕</button>
      </div>
      <div class="drawer-body">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup>
import { useResizableDrawer } from "@/composables/useResizableDrawer";

defineProps({
  visible: { type: Boolean, default: false },
});
defineEmits(["close"]);

const { width: drawerWidth, isResizing: resizing, startResize } = useResizableDrawer({
  direction: "right",
  minWidth: 280,
  maxWidth: 700,
  defaultWidth: 420,
});
</script>

<style scoped>
@import "@/assets/drawer.css";

.drawer-inner {
  flex: 1;
  background: #fff;
  border-left: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}
.drawer-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  white-space: nowrap;
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
</style>
