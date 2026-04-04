import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
export default defineConfig({
    plugins: [vue()],
    server: {
        host: "127.0.0.1",
        port: 5173,
        proxy: {
            "/api": {
                target: "http://127.0.0.1:8000",
                changeOrigin: true,
            },
        },
    },
    build: {
        rollupOptions: {
            output: {
                manualChunks(id) {
                    if (!id.includes("node_modules"))
                        return undefined;
                    if (id.includes("element-plus") || id.includes("@element-plus"))
                        return "element-plus";
                    if (id.includes("echarts"))
                        return "echarts";
                    if (id.includes("vue") || id.includes("pinia") || id.includes("vue-router"))
                        return "vue-vendor";
                    return "vendor";
                },
            },
        },
    },
});
