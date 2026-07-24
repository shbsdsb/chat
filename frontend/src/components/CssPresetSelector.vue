<template>
  <button
    class="css-icon-btn"
    @click="$emit('openDrawer')"
    title="自定义 CSS"
  >🎨</button>
</template>

<script setup>
defineEmits(["openDrawer"]);
</script>

<style>
.css-icon-btn {
  padding: 3px 6px;
  border: 1px solid #d5d5d5;
  border-radius: 6px;
  background: #fff;
  font-size: 13px;
  cursor: pointer;
}
.css-icon-btn:hover {
  background: #e8e8e8;
}
</style>
