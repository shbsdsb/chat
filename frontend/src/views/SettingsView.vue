<template>
  <div class="settings-page">
    <!-- 卡片1: 预设管理 -->
    <div class="card">
      <div class="card-header">
        <span class="card-icon"><Settings :size="18" /></span>
        <span class="card-label">预设</span>
      </div>
      <PresetSelector />
    </div>

    <!-- 卡片2: 连接信息 -->
    <div class="card">
      <div class="card-header">
        <span class="card-icon"><Plug :size="18" /></span>
        <span class="card-label">连接信息</span>
      </div>
      <div class="form-row">
        <span class="field-label">API URL</span>
        <input v-model="store.apiUrl" class="input-field input-mono" placeholder="https://api.openai.com/v1" />
      </div>
      <div class="form-row">
        <span class="field-label">API Key</span>
        <input v-model="store.apiKey" class="input-field input-mono" type="password" placeholder="sk-···" />
      </div>
    </div>

    <!-- 卡片3: 模型 -->
    <div class="card">
      <div class="card-header">
        <span class="card-icon"><MessageSquare :size="18" /></span>
        <span class="card-label">模型</span>
      </div>
      <ModelSelector />
    </div>

    <!-- 卡片4: 响应格式 -->
    <div class="card">
      <div class="card-header">
        <span class="card-icon"><Code :size="18" /></span>
        <span class="card-label">响应格式</span>
      </div>
      <ResponseFormatInput />
    </div>

    <!-- 状态指示行 -->
    <div class="status-bar">
      <div class="status-left">
        <span class="status-dot" :class="store.connectionStatus"></span>
        <span class="status-text" :class="{ connected: store.connectionStatus === 'connected' }">
          {{ statusLabel }}
        </span>
      </div>
      <div class="auto-connect-toggle" @click="store.autoConnect = !store.autoConnect">
        <div class="toggle-box" :class="{ on: store.autoConnect }">
          <svg v-if="store.autoConnect" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
        </div>
        <span class="toggle-label">自动连接</span>
      </div>
    </div>

    <!-- 测试按钮 -->
    <div class="test-section">
      <button class="test-btn" :disabled="testing || !store.apiUrl || !store.apiKey" @click="handleTestConnection">
        <span v-if="testing" class="btn-spinner"></span>
        <RefreshCw v-else :size="15" />
        {{ testing ? '测试中...' : (store.connectionStatus === 'connected' ? '重新测试' : '测试连接') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { Settings, Plug, MessageSquare, Code, RefreshCw } from "lucide-vue-next";
import { useSettingsStore } from "@/stores/settings";
import { useAlertStore } from "@/stores/alert";
import PresetSelector from "@/components/PresetSelector.vue";
import ModelSelector from "@/components/ModelSelector.vue";
import ResponseFormatInput from "@/components/ResponseFormatInput.vue";

const store = useSettingsStore();
const alert = useAlertStore();
const testing = ref(false);

const statusLabel = computed(() => {
  switch (store.connectionStatus) {
    case "testing": return "正在测试连接...";
    case "connected": return `已连接 · ${store.availableModels.length} 个模型可用`;
    default: return "未连接";
  }
});

onMounted(async () => {
  try {
    await store.loadPresets();
  } catch (e) {
    console.error("加载预设失败:", e);
  }
  // 自动连接
  if (store.autoConnect && store.apiUrl && store.apiKey) {
    handleTestConnection();
  }
});

async function handleTestConnection() {
  testing.value = true;
  store.connectionStatus = "testing";
  try {
    await store.fetchModels();
    store.connectionStatus = "connected";
  } catch (e) {
    store.connectionStatus = "disconnected";
    alert.error("连接失败", e.message || "请检查 API URL 和 Key 是否正确");
  } finally {
    testing.value = false;
  }
}
</script>

<style>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ——— 卡片 ——— */
.card {
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.card-icon {
  color: var(--card-icon-color);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
}
.card-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

/* ——— 表单控件 ——— */
.form-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 10px;
}
.form-row:last-child { margin-bottom: 0; }
.field-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}
.input-field {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--text-primary);
  background: var(--bg-input);
  outline: none;
  font-family: inherit;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.input-field:focus {
  border-color: var(--accent);
  box-shadow: var(--focus-ring);
}
.input-field::placeholder { color: var(--text-muted); }
.input-mono {
  font-family: "Consolas", "Monaco", monospace;
  font-size: 12px;
}

/* ——— 状态指示行 ——— */
.status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: var(--bg-input);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  gap: 12px;
}
.status-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  transition: background 0.3s;
}
.status-dot.disconnected { background: var(--status-dot-disconnected); }
.status-dot.connected { background: var(--status-dot-connected); }
.status-dot.testing {
  background: var(--accent);
  animation: pulse-dot 1s ease-in-out infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.7); }
}
.status-text {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
}
.status-text.connected { color: var(--success); font-weight: 500; }

/* ——— 自动连接开关 ——— */
.auto-connect-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  user-select: none;
  flex-shrink: 0;
}
.toggle-box {
  width: 18px;
  height: 18px;
  border: 2px solid var(--border);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  background: var(--bg-input);
}
.toggle-box.on {
  background: var(--toggle-bg-on);
  border-color: var(--toggle-bg-on);
}
.toggle-label {
  font-size: 12px;
  color: var(--text-muted);
  transition: color 0.15s;
}
.auto-connect-toggle:hover .toggle-label { color: var(--text-secondary); }
.auto-connect-toggle:hover .toggle-box:not(.on) { border-color: var(--border); }

/* ——— 测试按钮 ——— */
.test-section {
  display: flex;
  align-items: center;
  gap: 12px;
}
.test-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 8px 18px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--test-btn-bg);
  color: var(--test-btn-text);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s, transform 0.15s, box-shadow 0.15s;
  box-shadow: 0 1px 3px rgba(79,110,246,0.2);
}
.test-btn:hover:not(:disabled) {
  background: var(--accent-light);
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(79,110,246,0.3);
}
.test-btn:disabled {
  opacity: 0.45;
  cursor: default;
  transform: none;
  box-shadow: none;
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
