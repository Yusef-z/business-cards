import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { slugify, stripHonorific, normalizePhone } from "../src/lib/employees.js";

const ORG = "Al Watania Holding Group";
// Company-wide constants shown on every card (not present per-row in the source).
const WEBSITE = "https://www.alwatania-holding.com";
const LOCATION = "Baghdad, Baghdad Governorate Iraq";

// One-off corrections for known issues in the source CSV, keyed by the
// whitespace-collapsed original value. Explicit so they are reviewable.
const NAME_FIXES = { "KhloodOuda Al-Ameri": "Khlood Ouda Al-Ameri" };
const TITLE_FIXES = { "Projecs Engineer": "Projects Engineer" };

export function parseEmployeesCsv(csvText) {
  const lines = csvText.split(/\r?\n/).slice(1); // drop header
  return lines
    .filter((l) => l.trim())
    .map((line) => {
      const [rawName = "", rawTitle = "", rawEmail = "", rawPhone = ""] = line.split(",");
      const name0 = rawName.trim().replace(/\s+/g, " ");
      const name = NAME_FIXES[name0] || name0;
      const title0 = rawTitle.trim().replace(/\s+/g, " ");
      const title = TITLE_FIXES[title0] || title0;
      const email = rawEmail.trim();
      const phone = normalizePhone(rawPhone);
      const slug = slugify(stripHonorific(name));
      return { slug, name, title, org: ORG, email, phone, website: WEBSITE, location: LOCATION, photo: null };
    });
}

// Run directly (not when imported by the test): read the CSV, write the JSON.
if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  const dir = dirname(fileURLToPath(import.meta.url));
  const csv = readFileSync(resolve(dir, "../employees_list.csv"), "utf8");
  const employees = parseEmployeesCsv(csv);
  const out = resolve(dir, "../src/data/employees.json");
  writeFileSync(out, JSON.stringify(employees, null, 2) + "\n");
  console.log(`Wrote ${employees.length} employees to ${out}`);
}
