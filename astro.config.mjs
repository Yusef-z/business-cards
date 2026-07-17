import { defineConfig } from 'astro/config';

export default defineConfig({
  output: 'static',
  build: { format: 'directory' },
  trailingSlash: 'ignore',
  // GitHub Pages project site: https://yusef-z.github.io/business-cards/
  site: process.env.SITE_URL || "https://yusef-z.github.io",
  base: process.env.BASE_PATH || "/business-cards",
});
