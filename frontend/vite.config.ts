import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

// `npm run dev`: the page on http://localhost:5173, /api forwarded to FastAPI on port 8000.
// `npm run build`: plain files in dist/, served by FastAPI.
export default defineConfig({
  plugins: [vue()],
  server: { proxy: { "/api": "http://localhost:8000" } },
});
