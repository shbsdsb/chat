import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { readFileSync } from "fs";
import { dirname, resolve } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

const config = JSON.parse(
  readFileSync(resolve(__dirname, "vite.config.json"), "utf-8")
);

export default defineConfig({
  base: config.base || "./",
  plugins: [vue()],
  server: {
    host: config.server.host,
    port: config.server.port,
    proxy: {
      "/api": {
        target: config.proxy["/api"],
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      "@": resolve(__dirname, "src"),
    },
  },
});
