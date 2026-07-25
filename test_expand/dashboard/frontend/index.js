// Dashboard 扩展前端入口 — 纯脚本，由 ExtensionSlot 动态注入
(function() {
  var reg = window.__EXTENSION_REGISTRY__ || {};
  var comp = window.__DASHBOARD_FLOATING__;
  if (!comp) {
    console.warn('[dashboard] DashboardFloating 组件未预加载');
    return;
  }
  reg['dashboard'] = { panel: [comp] };
  window.__EXTENSION_REGISTRY__ = reg;
})();
