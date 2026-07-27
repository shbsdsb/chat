<template>
  <div id="app" class="app-shell">
    <header class="top-bar">
      <div class="top-left">
        <button class="top-btn" :class="{ active: showConversations }"
          @click="showConversations = !showConversations" title="会话记录">
          <Sidebar :size="18" />
        </button>
        <span class="top-title">Chat</span>
      </div>
      <nav class="top-nav">
        <button class="top-btn" :class="{ active: activeDrawer === 'css' }"
          @click="toggleDrawer('css')" title="CSS 预设">
          <Palette :size="18" />
        </button>
        <button class="top-btn" :class="{ active: activeDrawer === 'presets' }"
          @click="toggleDrawer('presets')" title="参数预设">
          <SlidersHorizontal :size="18" />
        </button>
        <button class="top-btn" :class="{ active: activeDrawer === 'api' }"
          @click="toggleDrawer('api')" title="API 设置">
          <Plug :size="18" />
        </button>
        <button class="top-btn" :class="{ active: activeDrawer === 'extensions' }"
          @click="toggleDrawer('extensions')" title="扩展管理">
          <Blocks :size="18" />
        </button>
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
          <ExtensionManager v-else-if="activeDrawer === 'extensions'" key="extensions" />
        </Transition>
      </SettingsDrawer>
    </div>
    <ExtensionSlot name="panel" />
    <AlertDialog />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import ConversationsDrawer from "@/components/ConversationsDrawer.vue";
import SettingsDrawer from "@/components/SettingsDrawer.vue";
import SettingsView from "@/views/SettingsView.vue";
import ParamPresetSelector from "@/components/ParamPresetSelector.vue";
import CssPresetEditor from "@/components/CssPresetEditor.vue";
import AlertDialog from "@/components/AlertDialog.vue";
import ExtensionManager from "@/components/ExtensionManager.vue";
import ExtensionSlot from "@/extensions/ExtensionSlot.vue";
import { Sidebar, Palette, SlidersHorizontal, Plug, Blocks } from "lucide-vue-next";
import { useChatStore } from "@/stores/chat";
import { useParamPresetsStore } from "@/stores/paramPresets";
import { useCssPresetsStore } from "@/stores/cssPresets";
import { useExtensionsStore } from "@/stores/extensions";

const chatStore = useChatStore();
const paramPresetsStore = useParamPresetsStore();
const cssPresetsStore = useCssPresetsStore();
const extensionsStore = useExtensionsStore();
const showConversations = ref(false);

// 单状态互斥：四个设置抽屉共用一个 activeDrawer
const activeDrawer = ref(null); // null | 'api' | 'presets' | 'css' | 'extensions'

const drawerTitles = { api: "API 设置", presets: "预设", css: "自定义 CSS", extensions: "扩展管理" };
const drawerTitle = computed(() => drawerTitles[activeDrawer.value] || "");

function toggleDrawer(name) {
  activeDrawer.value = activeDrawer.value === name ? null : name;
}

onMounted(() => {
  chatStore.loadConversations();
  paramPresetsStore.loadPresets();
  cssPresetsStore.loadPresets();
  extensionsStore.fetchExtensions();
});
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --bg-primary: #fff;
  --bg-secondary: #f8f9fb;
  --bg-tertiary: #f0f1f5;
  --text-primary: #1a1a2e;
  --text-secondary: #5b5b7a;
  --text-muted: #8e8ea0;
  --border: #e2e4eb;
  --border-light: #d8dae2;
  --accent: #4f6ef6;
  --accent-light: #6c8cfc;
  --danger: #ef4444;
  --shadow-xs: 0 1px 2px rgba(0,0,0,0.04);
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 16px rgba(0,0,0,0.08);
  --shadow-lg: 0 8px 32px rgba(0,0,0,0.10);
  --glass-bg: rgba(255,255,255,0.7);
  --glass-border: rgba(0,0,0,0.06);
  --glass-blur: 12px;
  --radius-sm: 8px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-xl: 28px;
}

html, body, #app {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: var(--text-primary);
  background: var(--bg-primary);
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
  height: 48px;
  padding: 0 20px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  box-shadow: var(--shadow-xs);
  flex-shrink: 0;
  position: relative;
  z-index: 10;
}

.top-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.top-title {
  font-size: 16px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent), #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.top-nav {
  display: flex;
  gap: 4px;
}

.top-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  position: relative;
  transition: all 0.15s ease;
}
.top-btn::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 2px;
  background: var(--accent);
  border-radius: 2px;
  transition: width 0.15s ease;
}
.top-btn:hover {
  color: var(--text-primary);
  transform: translateY(-1px);
}
.top-btn:hover::after {
  width: 60%;
}
/* 激活态 */
.top-btn.active {
  color: var(--text-primary);
}
.top-btn.active::after {
  width: 100%;
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
  background: var(--bg-primary);
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

/* ── 全局动画 @keyframes ────────────────── */

@keyframes message-enter {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes blink-cursor {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0; }
}

@keyframes ripple {
  from { transform: scale(0); opacity: 0.25; }
  to   { transform: scale(4); opacity: 0; }
}

@keyframes stop-pulse {
  0%   { box-shadow: 0 0 0 0 rgba(239,68,68,0.4); }
  100% { box-shadow: 0 0 0 8px rgba(239,68,68,0); }
}
</style>
