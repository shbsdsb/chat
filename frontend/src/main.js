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
