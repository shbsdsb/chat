import { createApp, h, ref, computed, watch, onMounted, onBeforeUnmount } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import "highlight.js/styles/github.css";

// 扩展系统全局注册表（扩展前端入口通过此对象注册组件）
window.__EXTENSION_REGISTRY__ = {};
window.__EXTENSION_SCRIPTS_LOADED__ = new Set();

// 暴露 Vue API 到全局，供动态加载的扩展组件使用
window.__EXT_VUE__ = { h, ref, computed, watch, onMounted, onBeforeUnmount };

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.mount("#app");

// ── 全局 Ripple 效果 ────────────────────────

document.addEventListener("mousedown", (e) => {
  const btn = e.target.closest(".btn-ripple");
  if (!btn) return;

  const ripple = document.createElement("span");
  ripple.className = "ripple";

  const rect = btn.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height);
  ripple.style.width = ripple.style.height = `${size}px`;
  ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
  ripple.style.top = `${e.clientY - rect.top - size / 2}px`;

  btn.appendChild(ripple);

  ripple.addEventListener("animationend", () => ripple.remove());
});

// 注入 ripple 全局样式
const rippleStyle = document.createElement("style");
rippleStyle.textContent = `
  .btn-ripple { position: relative; overflow: hidden; }
  .ripple {
    position: absolute;
    border-radius: 50%;
    background: rgba(255,255,255,0.3);
    pointer-events: none;
    animation: ripple 0.5s ease-out;
  }
`;
document.head.appendChild(rippleStyle);

// ── 消息入场动画 ────────────────────────────

const msgObserver = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    mutation.addedNodes.forEach((node) => {
      if (node.nodeType !== 1) return;
      // 新增的消息气泡行
      const bubbleRows = node.classList?.contains("bubble-row")
        ? [node]
        : node.querySelectorAll?.(".bubble-row") || [];

      bubbleRows.forEach((row) => {
        row.classList.add("entering");
        row.addEventListener("animationend", () => {
          row.classList.remove("entering");
        }, { once: true });
      });
    });
  });
});

// 延迟启动观察（等 DOM 就绪）
setTimeout(() => {
  const listEl = document.querySelector(".message-list");
  if (listEl) {
    msgObserver.observe(listEl, { childList: true, subtree: false });
  }
}, 500);
