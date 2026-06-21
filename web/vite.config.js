import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Dev server runs on 5173 (Keya's CORS + the plan both assume this port).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // Allow tunnel hosts (cloudflared / ngrok) so the Browserbase cloud browser can
    // reach the mock inbox/bank when running the executor with DEMO_MODE=0. Vite
    // otherwise rejects non-localhost Host headers with "host is not allowed".
    allowedHosts: [".trycloudflare.com", ".ngrok-free.app", ".ngrok.io", ".loca.lt"],
  },
});
