<template>
  <div
    class="conv-item"
    :class="{ active }"
    @click="$emit('select')"
    @contextmenu.prevent="showMenu = true"
  >
    <span class="conv-title">{{ conversation.title }}</span>
    <div v-if="showMenu" class="context-menu">
      <button @click.stop="startRename">重命名</button>
      <button @click.stop="$emit('delete')">删除</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

const props = defineProps({
  conversation: { type: Object, required: true },
  active: { type: Boolean, default: false },
});

const emit = defineEmits(["select", "delete", "rename"]);

const showMenu = ref(false);

function startRename() {
  showMenu.value = false;
  const title = prompt("新名称", props.conversation.title);
  if (title && title.trim()) {
    emit("rename", title.trim());
  }
}

document.addEventListener("click", () => {
  showMenu.value = false;
});
</script>

<style scoped>
.conv-item {
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  position: relative;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.conv-item:hover {
  background: #e8e8e8;
}
.conv-item.active {
  background: #fff;
  border: 1px solid #d5d5d5;
}

.conv-title {
  pointer-events: none;
}

.context-menu {
  position: absolute;
  top: 100%;
  left: 8px;
  background: #fff;
  border: 1px solid #d5d5d5;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  z-index: 10;
  overflow: hidden;
}
.context-menu button {
  display: block;
  width: 100%;
  padding: 6px 12px;
  border: none;
  background: #fff;
  color: #333;
  font-size: 13px;
  cursor: pointer;
  text-align: left;
}
.context-menu button:hover {
  background: #f5f5f5;
}
</style>
