import { defineStore } from "pinia";
import * as settingsApi from "@/api/settings";

export const useSettingsStore = defineStore("settings", {
  state: () => ({
    presets: [],
    activePresetId: null,
    loading: false,
    apiUrl: "",
    apiKey: "",
    model: "gpt-4o",
    responseFormat: "",
    availableModels: [],
  }),

  actions: {
    async loadPresets() {
      this.loading = true;
      try {
        this.presets = await settingsApi.list();
        if (!this.presets || !Array.isArray(this.presets)) {
          this.presets = [];
        }
        if (!this.activePresetId && this.presets.length > 0) {
          const def = this.presets.find((p) => p.is_default) || this.presets[0];
          if (def && def.id) {
            this.selectPreset(def.id);
          }
        }
        if (this.activePresetId && !this.presets.some((p) => p.id === this.activePresetId)) {
          if (this.presets.length > 0) {
            this.selectPreset(this.presets[0].id);
          } else {
            this.activePresetId = null;
          }
        }
      } catch (e) {
        this.presets = [];
        console.error("加载预设列表失败:", e);
        throw e;
      } finally {
        this.loading = false;
      }
    },

    selectPreset(id) {
      if (id == null) {
        this.activePresetId = null;
        return;
      }
      const preset = this.presets.find((p) => p.id === id);
      if (!preset) {
        console.warn("selectPreset: 未找到预设", id);
        return;
      }
      this.activePresetId = preset.id;
      this.apiUrl = preset.api_url || "";
      this.apiKey = preset.api_key || "";
      this.model = preset.model || "gpt-4o";
      this.responseFormat = preset.response_format || "";
    },

    async createPreset(name) {
      if (!name || !name.trim()) {
        throw new Error("预设名称不能为空");
      }
      if (!this.apiUrl || !this.apiUrl.trim()) {
        throw new Error("API URL 不能为空");
      }
      const key = this.apiKey || "";
      const preset = await settingsApi.create({
        name: name.trim(),
        api_url: this.apiUrl.trim(),
        api_key: key,
        model: this.model || "gpt-4o",
        response_format: this.responseFormat,
        temperature: 0.7,
        max_tokens: 4096,
      });
      if (!preset || !preset.id) {
        throw new Error("创建预设失败：服务器返回异常");
      }
      this.presets.push(preset);
      this.activePresetId = preset.id;
    },

    async savePreset() {
      if (!this.activePresetId) throw new Error("未选中任何预设");
      const payload = {
        api_url: this.apiUrl,
        model: this.model,
        response_format: this.responseFormat,
      };
      if (this.apiKey) {
        payload.api_key = this.apiKey;
      }
      const updated = await settingsApi.update(this.activePresetId, payload);
      if (!updated || !updated.id) {
        throw new Error("保存失败：服务器返回异常");
      }
      const idx = this.presets.findIndex((p) => p.id === this.activePresetId);
      if (idx !== -1) this.presets[idx] = updated;
    },

    async deletePreset(id) {
      if (!id) throw new Error("未指定要删除的预设");
      await settingsApi.remove(id);
      this.presets = this.presets.filter((p) => p.id !== id);
      if (this.activePresetId === id) {
        this.activePresetId = null;
        if (this.presets.length > 0) {
          this.selectPreset(this.presets[0].id);
        }
      }
    },

    async fetchModels() {
      const data = await settingsApi.fetchModels(this.apiUrl, this.apiKey);
      this.availableModels = data || [];
    },
  },
});
