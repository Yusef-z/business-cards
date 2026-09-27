import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { slugify, stripHonorific, normalizePhone } from "../src/lib/employees.js";

// One-off corrections for known issues in the source CSVs, keyed by the
// whitespace-collapsed original value. Explicit so they are reviewable.
const NAME_FIXES = { "KhloodOuda Al-Ameri": "Khlood Ouda Al-Ameri" };
const TITLE_FIXES = { "Projecs Engineer": "Projects Engineer" };

// `tenant` supplies the company-wide constants shown on every card
// (org, website, location) — they are not present per-row in the source.
export function parseEmployeesCsv(csvText, tenant) {
  const { org, website, location } = tenant;
  const lines = csvText.split(/\r?\n/).slice(1); // drop header
  return lines
    .filter((l) => l.trim())
    .map((line) => {
      const [rawName = "", rawTitle = "", rawEmail = "", rawPhone = "", rawPhone2 = ""] = line.split(",");
      const name0 = rawName.trim().replace(/\s+/g, " ");
      const name = NAME_FIXES[name0] || name0;
      const title0 = rawTitle.trim().replace(/\s+/g, " ");
      const title = TITLE_FIXES[title0] || title0;
      const email = rawEmail.trim();
      const phone = normalizePhone(rawPhone);
      const phone2 = rawPhone2.trim() ? normalizePhone(rawPhone2) : "";
      const slug = slugify(stripHonorific(name));
      return { slug, name, title, org, email, phone, phone2, website, location, photo: null };
    });
}

// Run directly (not when imported by the test): read the tenant's CSV, write its JSON.
// Usage: node scripts/build-employees.mjs [tenant-id]   (default: watania)
if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  const dir = dirname(fileURLToPath(import.meta.url));
  const id = process.argv[2] || "watania";
  const tdir = resolve(dir, `../tenants/${id}`);
  const tenant = JSON.parse(readFileSync(resolve(tdir, "tenant.json"), "utf8"));
  const csv = readFileSync(resolve(tdir, "employees.csv"), "utf8");
  const employees = parseEmployeesCsv(csv, tenant);

  // Auto-attach a photo when public/<team>/<slug>.<ext> exists (drop a file, re-run).
  const exts = ["jpg", "jpeg", "png", "webp"];
  for (const e of employees) {
    for (const ext of exts) {
      if (existsSync(resolve(dir, `../public${tenant.team}/${e.slug}.${ext}`))) {
        e.photo = `${tenant.team}/${e.slug}.${ext}`;
        break;
      }
    }
  }

  const out = resolve(tdir, "employees.json");
  writeFileSync(out, JSON.stringify(employees, null, 2) + "\n");
  console.log(`Wrote ${employees.length} employees to ${out}`);
}
