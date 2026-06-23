import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During `npm run dev`, requests to /api are proxied to the FastAPI backend,
// so the browser talks to a single origin (no CORS issues in development).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
