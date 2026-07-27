<template>
  <div class="welcome">
    <div class="welcome-bg"></div>
    <div class="welcome-content">
      <h1 class="welcome-title">Chat</h1>
      <p class="welcome-subtitle">智能对话，触手可及</p>
      <button class="btn-start btn-ripple" @click="chatStore.createConversation()">开始新对话</button>
      <div class="welcome-cards">
        <div class="welcome-card" @click="chatStore.createConversation()">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>
          <span>新对话</span>
        </div>
        <div class="welcome-card" @click="$router.push('/settings')">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          <span>设置</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useChatStore } from "@/stores/chat";
import { useRouter } from "vue-router";
const chatStore = useChatStore();
const router = useRouter();
</script>

<style scoped>
.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.welcome-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 80% 60% at 50% 40%, rgba(79,110,246,0.04) 0%, transparent 70%),
    radial-gradient(ellipse 40% 30% at 80% 20%, rgba(139,92,246,0.03) 0%, transparent 70%);
  pointer-events: none;
}

.welcome-content {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 1;
}

.welcome-title {
  font-size: 36px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--accent), #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}

.welcome-subtitle {
  font-size: 15px;
  color: var(--text-muted);
  margin-bottom: 28px;
}

.btn-start {
  padding: 12px 32px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--accent);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}
.btn-start:hover {
  background: #3d5ce5;
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}
.btn-start:active {
  transform: translateY(0);
}

.welcome-cards {
  display: flex;
  gap: 12px;
  margin-top: 36px;
}

.welcome-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 24px;
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  box-shadow: var(--shadow-xs);
  border: 1px solid var(--border);
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 13px;
  transition: all 0.2s ease;
  min-width: 100px;
}
.welcome-card:hover {
  box-shadow: var(--shadow-sm);
  transform: translateY(-2px);
  border-color: var(--accent);
  color: var(--accent);
}
</style>
