import { defineConfig } from 'astro/config';

export default defineConfig({
  output: 'static',
  build: { format: 'directory' },
  trailingSlash: 'ignore',
  // Served at the root of the custom domain https://areez-qr.com/ (GitHub Pages).
  // Override SITE_URL/BASE_PATH to build for a subpath (e.g. the github.io project site).
  site: process.env.SITE_URL || "https://areez-qr.com",
  base: process.env.BASE_PATH || "/",
  vite: {
    server: {
      // Allow the dev server to be reached through this ngrok tunnel.
      allowedHosts: ["sparrow-assured-repeatedly.ngrok-free.app"],
    },
  },
});
