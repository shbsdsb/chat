import { defineStore } from "pinia";
import * as settingsApi from "@/api/settings";

export const useSettingsStore = defineStore("settings", {
  state: () => ({
    presets: [],
    activePresetId: null,
    apiUrl: "",
    apiKey: "",
    model: "gpt-4o",
    responseFormat: "",
    availableModels: [],
  }),

  actions: {
    async loadPresets() {
      this.presets = await settingsApi.list();
      if (!this.activePresetId && this.presets.length > 0) {
        const def = this.presets.find((p) => p.is_default) || this.presets[0];
        this.selectPreset(def.id);
      }
    },

    selectPreset(id) {
      const preset = this.presets.find((p) => p.id === id);
      if (!preset) return;
      this.activePresetId = preset.id;
      this.apiUrl = preset.api_url;
      this.apiKey = preset.api_key;
      this.model = preset.model;
      this.responseFormat = preset.response_format;
    },

    async createPreset(name) {
      const preset = await settingsApi.create({
        name,
        api_url: "https://api.openai.com/v1",
        api_key: "",
        model: "gpt-4o",
        response_format: "text",
        temperature: 0.7,
        max_tokens: 4096,
      });
      this.presets.push(preset);
      this.selectPreset(preset.id);
    },

    async savePreset() {
      if (!this.activePresetId) return;
      const updated = await settingsApi.update(this.activePresetId, {
        api_url: this.apiUrl,
        api_key: this.apiKey,
        model: this.model,
        response_format: this.responseFormat,
      });
      const idx = this.presets.findIndex((p) => p.id === this.activePresetId);
      if (idx !== -1) this.presets[idx] = updated;
    },

    async deletePreset(id) {
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
