const { contextBridge } = require("electron");

// 前端可通过 window.electronAPI 访问
contextBridge.exposeInMainWorld("electronAPI", {
  platform: process.platform,
  isElectron: true,
});
