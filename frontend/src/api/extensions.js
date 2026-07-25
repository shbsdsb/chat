// frontend/src/api/extensions.js
import http from './request.js';

export const extensionsApi = {
  list() {
    return http.get('/extensions');
  },
  getManifest(extId) {
    return http.get(`/extensions/${extId}/manifest`);
  },
  installZip(file) {
    const formData = new FormData();
    formData.append('install_method', 'zip');
    formData.append('file', file);
    return http.post('/extensions/install', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  installGit(gitUrl, branch = 'main') {
    const formData = new FormData();
    formData.append('install_method', 'git');
    formData.append('git_url', gitUrl);
    formData.append('git_branch', branch);
    return http.post('/extensions/install', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  confirm(extId, permissions) {
    return http.post(`/extensions/${extId}/confirm`, { permissions });
  },
  uninstall(extId) {
    return http.post(`/extensions/${extId}/uninstall`);
  },
  update(extId) {
    return http.post(`/extensions/${extId}/update`);
  },
  toggle(extId, enabled) {
    return http.post(`/extensions/${extId}/toggle`, { enabled });
  },
};
