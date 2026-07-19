import { defineStore } from "pinia";

export const useAlertStore = defineStore("alert", {
  state: () => ({
    visible: false,
    title: "",
    message: "",
    type: "info", // "info" | "error" | "warning" | "success"
  }),

  actions: {
    show(title, message, type = "info") {
      this.title = title;
      this.message = message;
      this.type = type;
      this.visible = true;
    },

    error(title, message) {
      this.show(title, message, "error");
    },

    warning(title, message) {
      this.show(title, message, "warning");
    },

    info(title, message) {
      this.show(title, message, "info");
    },

    success(title, message) {
      this.show(title, message, "success");
    },

    close() {
      this.visible = false;
    },
  },
});
