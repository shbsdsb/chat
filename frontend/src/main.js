import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import "highlight.js/styles/github.css";

// 扩展系统全局注册表（扩展前端入口通过此对象注册组件）
window.__EXTENSION_REGISTRY__ = {};

// 临时：手动注册内置扩展（后续改为自动加载机制）
import DashboardFloating from "../../test_expand/dashboard/frontend/components/DashboardFloating.js";
window.__EXTENSION_REGISTRY__["dashboard"] = {
  panel: [DashboardFloating],
};

const app = createApp(App);

app.use(createPinia());
app.use(router);
app.mount("#app");
