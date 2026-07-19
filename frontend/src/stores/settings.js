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
        // 仅当没有选中预设且列表非空时自动选中
        if (!this.activePresetId && this.presets.length > 0) {
          const def = this.presets.find((p) => p.is_default) || this.presets[0];
          if (def && def.id) {
            this.selectPreset(def.id);
          }
        }
        // 如果当前选中的预设已不在列表中，切换到第一个
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
        throw e;  // 让上层（组件）处理 toast 提示
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
      // 脱敏值禁止作为 API Key 提交（例如从旧预设加载的 "sk-1****"）
      const key = this.apiKey || "";
      if (key.includes("****")) {
        throw new Error("请重新输入完整的 API Key（当前为脱敏值）");
      }
      const preset = await settingsApi.create({
        name: name.trim(),
        api_url: this.apiUrl.trim(),
        api_key: key,
        model: this.model || "gpt-4o",
        response_format: this.responseFormat || "text",
        temperature: 0.7,
        max_tokens: 4096,
      });
      if (!preset || !preset.id) {
        throw new Error("创建预设失败：服务器返回异常");
      }
      this.presets.push(preset);
      this.selectPreset(preset.id);
    },

    async savePreset() {
      if (!this.activePresetId) throw new Error("未选中任何预设");
      const payload = {
        api_url: this.apiUrl,
        model: this.model,
        response_format: this.responseFormat,
      };
      // 仅当用户修改过 API Key（不含脱敏标记）时才发送，避免脱敏值覆盖原始 key
      if (this.apiKey && !this.apiKey.includes("****")) {
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
