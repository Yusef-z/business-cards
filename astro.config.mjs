import { defineConfig } from 'astro/config';

export default defineConfig({
  output: 'static',
  build: { format: 'directory' },
  trailingSlash: 'ignore',
  site: process.env.SITE_URL || "https://example.com",
});
