import { mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import QRCode from "qrcode";
import employees from "../src/data/employees.json" with { type: "json" };

// Defaults mirror astro.config.mjs; override via env for other deploys.
const SITE = (process.env.SITE_URL || "https://yusef-z.github.io").replace(/\/$/, "");
const BASE = process.env.BASE_PATH || "/business-cards";

const dir = dirname(fileURLToPath(import.meta.url));
const outDir = resolve(dir, "../qrcodes/e");
mkdirSync(outDir, { recursive: true });

for (const e of employees) {
  const url = `${SITE}${BASE}/e/${e.slug}`;
  await QRCode.toFile(resolve(outDir, `${e.slug}.png`), url, {
    width: 800,
    margin: 2,
    color: { dark: "#003349ff", light: "#ffffffff" },
  });
  console.log(`${e.slug} -> ${url}`);
}
console.log(`Wrote ${employees.length} QR codes to ${outDir}`);
