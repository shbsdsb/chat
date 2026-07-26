// frontend/src/stores/extensions.js
import { defineStore } from 'pinia';
import { extensionsApi } from '@/api/extensions';

export const useExtensionsStore = defineStore('extensions', {
  state: () => ({
    items: [],               // [{ id, name, description, version, enabled, ... }]
    pendingApproval: null,   // 待审批的扩展信息
    loading: false,
    detailExt: null,        // 当前查看详情的扩展对象
    detailSettings: null,   // { features: {...} }
    detailLoading: false,
    settingsVersion: 0,     // 递增以通知 ExtensionSlot 重新加载 settings
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

    async openDetail(ext) {
      this.detailExt = ext;
      this.detailLoading = true;
      try {
        this.detailSettings = await extensionsApi.getSettings(ext.id);
      } catch {
        this.detailSettings = { features: {} };
      } finally {
        this.detailLoading = false;
      }
    },

    closeDetail() {
      this.detailExt = null;
      this.detailSettings = null;
    },

    async toggleFeature(extId, featureId, value) {
      const prevFeatures = { ...this.detailSettings?.features || {} };

      if (this.detailSettings?.features) {
        this.detailSettings.features[featureId] = value;
      }

      // 检查是否为 group 开关 → 级联子功能
      try {
        const manifest = await extensionsApi.getManifest(extId);
        const allFeatures = manifest?.features || [];
        const group = allFeatures.find(
          f => f.id === featureId && f.type === 'group'
        );
        if (group && this.detailSettings?.features) {
          for (const child of group.children || []) {
            const ck = `${featureId}.${child.id}`;
            if (!value) {
              this.detailSettings.features[ck] = false;
            }
          }
        }
      } catch {
        // manifest 获取失败时仅操作 featureId 本身
      }

      try {
        await extensionsApi.saveSettings(extId, this.detailSettings);
        this.settingsVersion++;
      } catch (e) {
        if (this.detailSettings?.features) {
          this.detailSettings.features = prevFeatures;
        }
        throw e;
      }
    },
  },
});
