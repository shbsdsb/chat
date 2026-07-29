// frontend/src/stores/promptEntries.js
import { defineStore } from "pinia";
import * as promptEntriesApi from "@/api/promptEntries";
import { useParamPresetsStore } from "@/stores/paramPresets";

export const usePromptEntriesStore = defineStore("promptEntries", {
  state: () => ({
    entries: [],
    loading: false,
  }),

  getters: {
    enabledEntries(state) {
      return state.entries.filter((e) => e.enabled);
    },
  },

  actions: {
    async loadEntries(presetId) {
      if (!presetId) {
        this.entries = [];
        return;
      }
      this.loading = true;
      try {
        this.entries = await promptEntriesApi.getEntries(presetId);
      } catch {
        this.entries = [];
      } finally {
        this.loading = false;
      }
    },

    async createEntry(name) {
      const presetId = useParamPresetsStore().activePresetId;
      if (!presetId) return;
      const entry = await promptEntriesApi.createEntry(presetId, name);
      this.entries.push(entry);
      return entry;
    },

    async updateEntry(id, data) {
      const presetId = useParamPresetsStore().activePresetId;
      if (!presetId) return;
      const entry = await promptEntriesApi.updateEntry(id, presetId, data);
      const idx = this.entries.findIndex((e) => e.id === id);
      if (idx !== -1) this.entries[idx] = entry;
      return entry;
    },

    async deleteEntry(id) {
      const presetId = useParamPresetsStore().activePresetId;
      if (!presetId) return;
      await promptEntriesApi.deleteEntry(id, presetId);
      this.entries = this.entries.filter((e) => e.id !== id);
    },

    async reorderEntries(ids) {
      const presetId = useParamPresetsStore().activePresetId;
      if (!presetId) return;
      // 乐观更新本地顺序
      const idToEntry = {};
      this.entries.forEach((e) => {
        idToEntry[e.id] = e;
      });
      const reordered = ids.map((id, i) => ({
        ...idToEntry[id],
        order: i,
      }));
      // 保留 __chat_history__ 占位符（不在 ids 中，需追加）
      const chatHistory = this.entries.find(e => e.id === "__chat_history__");
      if (chatHistory) {
        reordered.push({ ...chatHistory, order: reordered.length });
      }
      this.entries = reordered;
      // 后端同步
      await promptEntriesApi.reorderEntries(presetId, ids);
    },
  },
});
