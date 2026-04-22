/// <reference types="vitest/config" />

import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const apiTarget = process.env.LOCAL_EDU_API_BASE_URL ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [vue()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: "node",
    include: ["tests/**/*.test.ts"],
    clearMocks: true,
    restoreMocks: true,
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) return undefined;
          if (id.includes("element-plus") || id.includes("@element-plus")) return "element-plus";
          if (id.includes("echarts")) return "echarts";
          if (id.includes("vue") || id.includes("pinia") || id.includes("vue-router")) return "vue-vendor";
          return "vendor";
        },
      },
    },
  },
});
