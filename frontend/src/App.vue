<template>
  <div id="app" class="app-shell">
    <header class="top-bar">
      <div class="top-left">
        <button class="top-btn" @click="showConversations = !showConversations">会话记录</button>
        <span class="top-title">Chat</span>
      </div>
      <nav class="top-nav">
        <CssPresetSelector @open-drawer="openDrawer('css')" />
        <button class="top-btn" @click="toggleDrawer('presets')">预设</button>
        <button class="top-btn" @click="toggleDrawer('api')">API 设置</button>
      </nav>
    </header>
    <div class="app-body">
      <ConversationsDrawer :visible="showConversations" @close="showConversations = false" />
      <main class="main-area">
        <router-view />
      </main>
      <SettingsDrawer
        :visible="activeDrawer !== null"
        @close="activeDrawer = null"
      >
        <template #title>
          <Transition name="title-fade" mode="out-in">
            <span :key="activeDrawer">{{ drawerTitle }}</span>
          </Transition>
        </template>
        <Transition name="drawer-slide" mode="out-in">
          <SettingsView v-if="activeDrawer === 'api'" key="api" @saved="activeDrawer = null" />
          <ParamPresetSelector v-else-if="activeDrawer === 'presets'" key="presets" @saved="activeDrawer = null" />
          <CssPresetEditor v-else-if="activeDrawer === 'css'" key="css" />
        </Transition>
      </SettingsDrawer>
    </div>
    <AlertDialog />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import ConversationsDrawer from "@/components/ConversationsDrawer.vue";
import SettingsDrawer from "@/components/SettingsDrawer.vue";
import SettingsView from "@/views/SettingsView.vue";
import ParamPresetSelector from "@/components/ParamPresetSelector.vue";
import CssPresetSelector from "@/components/CssPresetSelector.vue";
import CssPresetEditor from "@/components/CssPresetEditor.vue";
import AlertDialog from "@/components/AlertDialog.vue";
import { useChatStore } from "@/stores/chat";
import { useParamPresetsStore } from "@/stores/paramPresets";
import { useCssPresetsStore } from "@/stores/cssPresets";

const chatStore = useChatStore();
const paramPresetsStore = useParamPresetsStore();
const cssPresetsStore = useCssPresetsStore();
const showConversations = ref(false);

// 单状态互斥：三个设置抽屉共用一个 activeDrawer
const activeDrawer = ref(null); // null | 'api' | 'presets' | 'css'

const drawerTitles = { api: "API 设置", presets: "预设", css: "自定义 CSS" };
const drawerTitle = computed(() => drawerTitles[activeDrawer.value] || "");

function toggleDrawer(name) {
  activeDrawer.value = activeDrawer.value === name ? null : name;
}
function openDrawer(name) {
  activeDrawer.value = name;
}

onMounted(() => {
  chatStore.loadConversations();
  paramPresetsStore.loadPresets();
  cssPresetsStore.loadPresets();
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

/* ── 抽屉内容切换动画 ────────────────── */
.drawer-slide-enter-active,
.drawer-slide-leave-active {
  transition: all 0.2s ease;
}
.drawer-slide-enter-from {
  transform: translateX(60px);
  opacity: 0;
}
.drawer-slide-leave-to {
  transform: translateX(-40px);
  opacity: 0;
}

.title-fade-enter-active,
.title-fade-leave-active {
  transition: opacity 0.15s ease;
}
.title-fade-enter-from,
.title-fade-leave-to {
  opacity: 0;
}
</style>
