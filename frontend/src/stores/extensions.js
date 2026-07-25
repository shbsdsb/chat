// frontend/src/stores/extensions.js
import { defineStore } from 'pinia';
import { extensionsApi } from '@/api/extensions';

export const useExtensionsStore = defineStore('extensions', {
  state: () => ({
    items: [],               // [{ id, name, description, version, enabled, ... }]
    pendingApproval: null,   // 待审批的扩展信息
    loading: false,
  }),

  getters: {
    enabledExtensions: (state) => state.items.filter(e => e.enabled),
    enabledIds: (state) => state.items.filter(e => e.enabled).map(e => e.id),
  },

  actions: {
    async fetchExtensions() {
      this.loading = true;
      try {
        this.items = await extensionsApi.list();
      } finally {
        this.loading = false;
      }
    },

    async installZip(file) {
      const result = await extensionsApi.installZip(file);
      this.pendingApproval = result;
      return result;
    },

    async installGit(url, branch) {
      const result = await extensionsApi.installGit(url, branch);
      this.pendingApproval = result;
      return result;
    },

    async confirmInstall(permissions) {
      const extId = this.pendingApproval.id;
      await extensionsApi.confirm(extId, permissions);
      this.pendingApproval = null;
      await this.fetchExtensions();
    },

    cancelInstall() {
      this.pendingApproval = null;
    },

    async uninstall(extId) {
      await extensionsApi.uninstall(extId);
      await this.fetchExtensions();
    },

    async update(extId) {
      await extensionsApi.update(extId);
      await this.fetchExtensions();
    },

    async toggle(extId, enabled) {
      await extensionsApi.toggle(extId, enabled);
      await this.fetchExtensions();
    },
  },
});
