import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import "highlight.js/styles/github.css";

// 扩展系统全局注册表（扩展前端入口通过此对象注册组件）
window.__EXTENSION_REGISTRY__ = {};

const app = createApp(App);

app.use(createPinia());
app.use(router);
app.mount("#app");
