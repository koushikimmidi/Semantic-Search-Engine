import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), "");

    // Backend the dev server forwards /api/* to. Override with
    // VITE_BACKEND_URL (e.g. in .env.local) if it runs elsewhere.
    const backend = env.VITE_BACKEND_URL || "http://127.0.0.1:8000";

    return {
        plugins: [react()],
        server: {
            proxy: {
                "/api": {
                    target: backend,
                    changeOrigin: true,
                    rewrite: (path) => path.replace(/^\/api/, "")
                }
            }
        }
    };
});
