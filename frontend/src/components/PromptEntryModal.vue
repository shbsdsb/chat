<template>
  <BaseDialog :visible="visible" :title="' '" @close="$emit('close')">
    <div class="em-body">
      <!-- 名称 + 消息归属 并排 -->
      <div class="em-row-inline">
        <div class="em-field">
          <label class="em-label">名称</label>
          <input v-model="form.name" class="em-input" placeholder="条目名称" />
        </div>
        <div class="em-field">
          <label class="em-label">消息归属</label>
          <select v-model="form.role" class="em-input">
            <option :value="null">无</option>
            <option value="system">系统</option>
            <option value="user">用户</option>
            <option value="assistant">AI消息</option>
          </select>
        </div>
      </div>

      <!-- 提示词内容 -->
      <div class="em-field">
        <label class="em-label">提示词内容</label>
        <textarea
          v-model="form.content"
          class="em-textarea"
          placeholder="输入提示词内容..."
          rows="8"
        ></textarea>
      </div>
    </div>

    <template #footer>
      <button class="dialog-btn dialog-btn-cancel" @click="$emit('close')">✕ 取消</button>
      <button class="dialog-btn dialog-btn-danger" @click="showDeleteConfirm = true">删除</button>
      <button class="dialog-btn dialog-btn-ok" @click="handleSave">保存</button>
    </template>
  </BaseDialog>

  <!-- 删除二次确认 -->
  <BaseDialog :visible="showDeleteConfirm" :title="' '" @close="showDeleteConfirm = false">
    <div class="dialog-danger">
      <p class="dialog-danger-msg">确定要删除条目「{{ form.name }}」吗？此操作不可撤销。</p>
    </div>
    <template #footer>
      <button class="dialog-btn dialog-btn-cancel" @click="showDeleteConfirm = false">取消</button>
      <button class="dialog-btn dialog-btn-danger" @click="handleDelete">确定删除</button>
    </template>
  </BaseDialog>
</template>

<script setup>
import { reactive, ref, watch } from "vue";
import BaseDialog from "@/components/BaseDialog.vue";

const props = defineProps({
  visible: { type: Boolean, default: false },
  entry: { type: Object, default: () => ({}) },
});

const emit = defineEmits(["close", "save", "delete"]);

const showDeleteConfirm = ref(false);

const form = reactive({
  name: "",
  content: "",
  role: null,
});

watch(
  () => props.visible,
  (val) => {
    if (val && props.entry) {
      form.name = props.entry.name || "";
      form.content = props.entry.content || "";
      form.role = props.entry.role || null;
      showDeleteConfirm.value = false;
    }
  }
);

function handleSave() {
  emit("save", {
    name: form.name.trim(),
    content: form.content,
    role: form.role,
  });
}

function handleDelete() {
  showDeleteConfirm.value = false;
  emit("delete", props.entry.id);
}
</script>

<style scoped>
.em-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.em-row-inline {
  display: flex;
  gap: 12px;
}
.em-row-inline > .em-field {
  flex: 1;
}
.em-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.em-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}
.em-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--text-primary);
  background: var(--bg-input);
  outline: none;
  font-family: inherit;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.em-input:focus {
  border-color: var(--accent);
  box-shadow: var(--focus-ring);
}
.em-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--text-primary);
  background: var(--bg-input);
  outline: none;
  font-family: inherit;
  line-height: 1.6;
  resize: vertical;
  min-height: 140px;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.em-textarea:focus {
  border-color: var(--accent);
  box-shadow: var(--focus-ring);
}
</style>
