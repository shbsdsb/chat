<template>
  <Teleport to="body">
    <transition name="alert-fade">
      <div v-if="store.visible" class="alert-overlay" @click.self="store.close()">
        <div class="alert-box" :class="'alert-' + store.type">
          <div class="alert-icon">
            <!-- error -->
            <svg v-if="store.type === 'error'" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#ef5350" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
            <!-- warning -->
            <svg v-else-if="store.type === 'warning'" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            <!-- success -->
            <svg v-else-if="store.type === 'success'" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            <!-- info -->
            <svg v-else width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4a90d9" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
          </div>
          <div class="alert-title">{{ store.title }}</div>
          <p class="alert-msg">{{ store.message }}</p>
          <button class="alert-btn" :class="'alert-btn-' + store.type" @click="store.close()">确定</button>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { useAlertStore } from "@/stores/alert";
const store = useAlertStore();
</script>

<style scoped>
.alert-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.alert-box {
  background: #fff;
  border-radius: 12px;
  padding: 28px 24px 20px;
  width: 360px;
  max-width: 90vw;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.18);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  text-align: center;
}

.alert-icon {
  display: flex;
  justify-content: center;
}

.alert-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.alert-msg {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin: 0;
}

.alert-btn {
  margin-top: 6px;
  padding: 8px 36px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  color: #fff;
  transition: background 0.15s;
  font-family: inherit;
}

.alert-btn-error  { background: #ef5350; }
.alert-btn-error:hover  { background: #d32f2f; }
.alert-btn-warning { background: #f59e0b; }
.alert-btn-warning:hover { background: #d97706; }
.alert-btn-info    { background: #4a90d9; }
.alert-btn-info:hover    { background: #357abd; }
.alert-btn-success { background: #22c55e; }
.alert-btn-success:hover { background: #16a34a; }

/* 顶部色条 */
.alert-error  { border-top: 3px solid #ef5350; }
.alert-warning { border-top: 3px solid #f59e0b; }
.alert-info    { border-top: 3px solid #4a90d9; }
.alert-success { border-top: 3px solid #22c55e; }

.alert-fade-enter-active,
.alert-fade-leave-active {
  transition: opacity 0.2s;
}
.alert-fade-enter-from,
.alert-fade-leave-to {
  opacity: 0;
}
</style>
