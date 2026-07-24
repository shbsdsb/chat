import { defineStore } from "pinia";
import * as cssPresetsApi from "@/api/cssPresets";

export const useCssPresetsStore = defineStore("cssPresets", {
  state: () => ({
    presets: [],
    activeId: null,
    loading: false,
  }),

  getters: {
    activePreset() {
      return this.presets.find((p) => p.id === this.activeId) || null;
    },
    activeContent() {
      const p = this.activePreset;
      return p ? p.content : "";
    },
  },

  actions: {
    /**
     * 加载预设列表，自动选中默认预设并注入 CSS
     */
    async loadPresets() {
      this.loading = true;
      try {
        this.presets = await cssPresetsApi.list();
        if (!this.presets || !Array.isArray(this.presets)) {
          this.presets = [];
        }
        if (!this.activeId && this.presets.length > 0) {
          const def = this.presets.find((p) => p.is_default) || this.presets[0];
          if (def && def.id) {
            this.activeId = def.id;
          }
        }
        if (this.activeId && !this.presets.some((p) => p.id === this.activeId)) {
          if (this.presets.length > 0) {
            this.activeId = this.presets[0].id;
          } else {
            this.activeId = null;
          }
        }
        // 注入 CSS
        this._injectCss();
      } catch (e) {
        this.presets = [];
        console.error("加载 CSS 预设列表失败:", e);
        throw e;
      } finally {
        this.loading = false;
      }
    },

    /**
     * 切换预设 — 立即替换页面 CSS
     */
    selectPreset(id) {
      if (id == null) {
        this.activeId = null;
        this._injectCss();
        return;
      }
      if (this.presets.find((p) => p.id === id)) {
        this.activeId = id;
        this._injectCss();
      }
    },

    /**
     * 实时更新 CSS（不持久化）
     */
    updateLiveCss(content) {
      this._injectCss(content);
    },

    async createPreset(name) {
      if (!name || !name.trim()) throw new Error("预设名称不能为空");
      const preset = await cssPresetsApi.create({
        name: name.trim(),
        content: "",
      });
      if (!preset || !preset.id) throw new Error("创建预设失败");
      this.presets.push(preset);
      this.activeId = preset.id;
      this._injectCss();
    },

    async savePreset(name, content) {
      if (!this.activeId) throw new Error("未选中任何预设");
      const updated = await cssPresetsApi.update(this.activeId, {
        name: (name || "").trim(),
        content: content || "",
      });
      if (!updated || !updated.id) throw new Error("保存失败");
      const idx = this.presets.findIndex((p) => p.id === this.activeId);
      if (idx !== -1) this.presets[idx] = updated;
    },

    async deletePreset(id) {
      if (!id) throw new Error("未指定要删除的预设");
      await cssPresetsApi.remove(id);
      this.presets = this.presets.filter((p) => p.id !== id);
      if (this.activeId === id) {
        this.activeId = null;
        if (this.presets.length > 0) {
          this.activeId = this.presets[0].id;
        }
        this._injectCss();
      }
    },

    // ── 内部：DOM 注入 ──────────────────────────

    _injectCss(content) {
      const css = content !== undefined ? content : this.activeContent;
      let styleEl = document.getElementById("custom-css");
      if (!styleEl) {
        styleEl = document.createElement("style");
        styleEl.id = "custom-css";
        document.head.appendChild(styleEl);
      }
      // 提取 @import 行，防止后续正则误伤 URL（如 @import url(https://...)）
      const imports = [];
      const withoutImports = css.replace(/@import\s+[^;]+;/g, (m) => {
        imports.push(m);
        return "";
      });
      // 对每条 CSS 声明追加 !important，以覆盖 Vue scoped 的 [data-v-xxxx] 属性选择器
      const processed = withoutImports.replace(
        /([\w-]+)\s*:\s*([^;{}]+?)(\s*[;}])/g,
        (match, prop, val, end) => {
          if (/!important/.test(val)) return match;
          return `${prop}: ${val.trimEnd()} !important${end}`;
        }
      );
      styleEl.textContent = imports.join("\n") + processed;
    },
  },
});
