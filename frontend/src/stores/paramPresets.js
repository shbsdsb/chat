import { defineStore } from "pinia";
import * as paramPresetsApi from "@/api/paramPresets";

export const useParamPresetsStore = defineStore("paramPresets", {
  state: () => ({
    presets: [],
    activePresetId: null,
    loading: false,
  }),

  getters: {
    activePreset() {
      return this.presets.find((p) => p.id === this.activePresetId) || null;
    },
    temperature() {
      const p = this.activePreset;
      return p ? p.temperature : 0.7;
    },
    maxTokens() {
      const p = this.activePreset;
      return p ? p.max_tokens : 4096;
    },
    topP() {
      const p = this.activePreset;
      return p ? p.top_p : 1.0;
    },
  },

  actions: {
    async loadPresets() {
      this.loading = true;
      try {
        this.presets = await paramPresetsApi.list();
        if (!this.presets || !Array.isArray(this.presets)) {
          this.presets = [];
        }
        if (!this.activePresetId && this.presets.length > 0) {
          const def = this.presets.find((p) => p.is_default) || this.presets[0];
          if (def && def.id) {
            this.activePresetId = def.id;
          }
        }
        if (this.activePresetId && !this.presets.some((p) => p.id === this.activePresetId)) {
          if (this.presets.length > 0) {
            this.activePresetId = this.presets[0].id;
          } else {
            this.activePresetId = null;
          }
        }
      } catch (e) {
        this.presets = [];
        console.error("加载参数预设列表失败:", e);
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
      if (this.presets.find((p) => p.id === id)) {
        this.activePresetId = id;
      }
    },

    async createPreset(name, temperature, maxTokens, topP) {
      if (!name || !name.trim()) throw new Error("预设名称不能为空");
      const preset = await paramPresetsApi.create({
        name: name.trim(),
        temperature,
        max_tokens: maxTokens,
        top_p: topP,
      });
      if (!preset || !preset.id) throw new Error("创建预设失败：服务器返回异常");
      this.presets.push(preset);
      this.activePresetId = preset.id;
    },

    async savePreset(temperature, maxTokens, topP) {
      if (!this.activePresetId) throw new Error("未选中任何预设");
      const preset = this.activePreset;
      if (!preset) throw new Error("未选中任何预设");
      const updated = await paramPresetsApi.update(this.activePresetId, {
        name: preset.name,
        temperature,
        max_tokens: maxTokens,
        top_p: topP,
      });
      if (!updated || !updated.id) throw new Error("保存失败：服务器返回异常");
      const idx = this.presets.findIndex((p) => p.id === this.activePresetId);
      if (idx !== -1) this.presets[idx] = updated;
    },

    async deletePreset(id) {
      if (!id) throw new Error("未指定要删除的预设");
      await paramPresetsApi.remove(id);
      this.presets = this.presets.filter((p) => p.id !== id);
      if (this.activePresetId === id) {
        this.activePresetId = null;
        if (this.presets.length > 0) {
          this.activePresetId = this.presets[0].id;
        }
      }
    },
  },
});
