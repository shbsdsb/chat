<template>
  <div id="app" class="app-shell">
    <header class="top-bar">
      <div class="top-left">
        <button class="top-btn" @click="showConversations = !showConversations">会话记录</button>
        <span class="top-title">Chat</span>
      </div>
      <nav class="top-nav">
        <button class="top-btn" @click="showParamPresets = !showParamPresets">预设</button>
        <button class="top-btn" @click="showSettings = !showSettings">API 设置</button>
      </nav>
    </header>
    <div class="app-body">
      <ConversationsDrawer :visible="showConversations" @close="showConversations = false" />
      <main class="main-area">
        <router-view />
      </main>
      <SettingsDrawer :visible="showParamPresets" @close="showParamPresets = false">
        <template #title>预设</template>
        <ParamPresetSelector @saved="showParamPresets = false" />
      </SettingsDrawer>
      <SettingsDrawer :visible="showSettings" @close="showSettings = false">
        <template #title>API 设置</template>
        <SettingsView @saved="showSettings = false" />
      </SettingsDrawer>
    </div>
    <AlertDialog />
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import ConversationsDrawer from "@/components/ConversationsDrawer.vue";
import SettingsDrawer from "@/components/SettingsDrawer.vue";
import SettingsView from "@/views/SettingsView.vue";
import ParamPresetSelector from "@/components/ParamPresetSelector.vue";
import AlertDialog from "@/components/AlertDialog.vue";
import { useChatStore } from "@/stores/chat";
import { useParamPresetsStore } from "@/stores/paramPresets";

const chatStore = useChatStore();
const paramPresetsStore = useParamPresetsStore();
const showConversations = ref(false);
const showSettings = ref(false);
const showParamPresets = ref(false);

onMounted(() => {
  chatStore.loadConversations();
  paramPresetsStore.loadPresets();
});
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: #333;
  background: #fff;
}

.app-shell {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 44px;
  padding: 0 16px;
  background: #fafafa;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}

.top-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.top-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.top-nav {
  display: flex;
  gap: 8px;
}

.top-btn {
  padding: 4px 12px;
  border: 1px solid #d5d5d5;
  border-radius: 6px;
  background: #fff;
  color: #555;
  font-size: 12px;
  cursor: pointer;
}
.top-btn:hover {
  background: #e8e8e8;
}

.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  overflow: hidden;
}
</style>
