import DashboardFloating from './components/DashboardFloating.js';

if (!window.__EXTENSION_REGISTRY__) {
  window.__EXTENSION_REGISTRY__ = {};
}
window.__EXTENSION_REGISTRY__['dashboard'] = {
  panel: [DashboardFloating],
};
