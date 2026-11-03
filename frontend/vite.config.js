import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Tutoia en desarrollo: `npm run dev` levanta Vite en :5173 y envía
// las llamadas /api al backend FastAPI en :8000.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false,
  },
});
