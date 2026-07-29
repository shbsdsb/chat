import { defineStore } from "pinia";
import * as presetsApi from "@/api/presets";

export const usePresetsStore = defineStore("presets", {
  state: () => ({
    presets: [],
    activePresetId: null,
    loading: false,
    entries: {},
  }),

  getters: {
    activePreset(state) {
      return state.presets.find((p) => p.id === state.activePresetId) || null;
    },
    temperature() {
      const p = this.activePreset;
      return p && p.temperature !== undefined ? p.temperature : 0.7;
    },
    maxTokens() {
      const p = this.activePreset;
      return p && p.max_tokens !== undefined ? p.max_tokens : 4096;
    },
    topP() {
      const p = this.activePreset;
      return p && p.top_p !== undefined ? p.top_p : 1.0;
    },
    params() {
      const p = this.activePreset;
      return p && p.params ? p.params : { temperature: 0.7, max_tokens: 4096, top_p: 1.0 };
    },
    entriesList(state) {
      const result = [];
      let idx = 0;
      for (const [key, value] of Object.entries(state.entries)) {
        if (key === "__chat_history__") {
          result.push({
            id: "__chat_history__",
            name: "对话历史",
            role: "system",
            content: "",
            enabled: true,
            order: idx,
          });
        } else if (typeof value === "object" && value !== null) {
          result.push({
            id: key,
            name: value.name || "",
            role: value.role,
            content: value.content || "",
            enabled: value.enabled !== false,
            order: idx,
          });
        }
        idx++;
      }
      return result;
    },
  },

  actions: {
    async loadPresets() {
      this.loading = true;
      try {
        const list = await presetsApi.list();
        this.presets = Array.isArray(list) ? list : [];
        if (!this.activePresetId && this.presets.length > 0) {
          const def = this.presets.find((p) => p.is_default) || this.presets[0];
          if (def && def.id) await this.selectPreset(def.id);
        }
      } catch (e) {
        this.presets = [];
        console.error("加载预设列表失败:", e);
      } finally {
        this.loading = false;
      }
    },

    async selectPreset(id) {
      if (!id) return;
      const preset = this.presets.find((p) => p.id === id);
      if (!preset) return;
      this.activePresetId = id;
      try {
        const detail = await presetsApi.get(id);
        this.entries = detail.entries || {};
        // 同时缓存 params 到索引
        if (detail.params) {
          const idx = this.presets.findIndex((p) => p.id === id);
          if (idx !== -1) {
            this.presets[idx] = {
              ...this.presets[idx],
              ...detail.params,
              name: detail.name,
              is_default: detail.is_default,
            };
          }
        }
      } catch (e) {
        this.entries = {};
      }
    },

    async createPreset(name, temperature, maxTokens, topP) {
      if (!name || !name.trim()) throw new Error("预设名称不能为空");
      const preset = await presetsApi.create({
        name: name.trim(), temperature, max_tokens: maxTokens, top_p: topP,
      });
      const idx = { id: preset.id, name: preset.name, is_default: false,
        temperature: temperature, max_tokens: maxTokens, top_p: topP };
      this.presets.push(idx);
      this.activePresetId = preset.id;
      this.entries = preset.entries || {};
    },

    async savePreset() {
      if (!this.activePresetId) throw new Error("未选中任何预设");
      const preset = this.activePreset;
      if (!preset) throw new Error("未选中任何预设");
      const updated = await presetsApi.update(this.activePresetId, {
        name: preset.name,
        params: {
          temperature: this.temperature,
          max_tokens: this.maxTokens,
          top_p: this.topP,
        },
        entries: this.entries,
      });
      const idx = this.presets.findIndex((p) => p.id === this.activePresetId);
      if (idx !== -1) {
        this.presets[idx] = {
          ...this.presets[idx],
          name: updated.name,
          is_default: updated.is_default,
          temperature: updated.params.temperature,
          max_tokens: updated.params.max_tokens,
          top_p: updated.params.top_p,
        };
      }
      return updated;
    },

    async deletePreset(id) {
      if (!id) throw new Error("未指定要删除的预设");
      await presetsApi.remove(id);
      this.presets = this.presets.filter((p) => p.id !== id);
      if (this.activePresetId === id) {
        this.activePresetId = null;
        this.entries = {};
        if (this.presets.length > 0) {
          const next = this.presets.find((p) => p.is_default) || this.presets[0];
          if (next) await this.selectPreset(next.id);
        }
      }
    },

    // ── 条目本地操作 ──
    addEntry(name) {
      const id = "temp-" + Date.now();
      const newEntries = { ...this.entries };
      newEntries[id] = { name, role: null, content: "", enabled: true };
      this.entries = newEntries;
      return id;
    },

    updateEntry(id, data) {
      const newEntries = { ...this.entries };
      if (newEntries[id] && typeof newEntries[id] === "object") {
        Object.assign(newEntries[id], data);
        this.entries = newEntries;
      }
    },

    removeEntry(id) {
      const newEntries = {};
      for (const [key, value] of Object.entries(this.entries)) {
        if (key !== id) newEntries[key] = value;
      }
      this.entries = newEntries;
    },

    reorderEntries(orderedIds) {
      const newEntries = {};
      for (const id of orderedIds) {
        if (id === "__chat_history__") {
          newEntries["__chat_history__"] = "chat_history";
        } else if (this.entries[id]) {
          newEntries[id] = this.entries[id];
        }
      }
      this.entries = newEntries;
    },
  },
});
