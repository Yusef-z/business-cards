# Al Watania Employee Cards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add per-individual employee business cards at `/e/<slug>` for Al Watania Holding Group, fully isolated from the existing 22 association cards.

**Architecture:** New `e/` route namespace with its own LTR/English layout, Changa font, and Watania petrol/green identity. Pure string logic (slug, phone, vCard) lives in one shared, unit-tested JS module reused by a CSV→JSON generator, the card components, and the vCard endpoint. Cards, a team index, vCards, and QR codes are all static build output — zero runtime JS.

**Tech Stack:** Astro 5 (static), `@fontsource/changa`, Vitest (unit tests), `qrcode` (QR script), Node scripts for data/QR generation, Python + poppler for one-time logo extraction.

## Global Constraints

- **Do not modify** any association code: `src/data/associations.json`, `src/components/Card.astro`, `src/layouts/Base.astro`, `src/styles/global.css`, `src/pages/index.astro`, `src/pages/[slug].astro`, `src/pages/vcards/[slug].vcf.ts`.
- **Node 22+** (repo targets Node 22 on Netlify; local is 24). JSON imports use `with { type: "json" }`.
- **URL namespace:** cards at `/e/<slug>`, index at `/e`, vCards at `/e/vcards/<slug>.vcf`.
- **Slugs are immutable** — they are printed in QR codes. Slug = kebab-case of the full name (honorific stripped).
- **Org constant:** `Al Watania Holding Group` on every card.
- **Brand colors:** Petrol Blue `#003349`, Grass Green `#6ABF4B`, Light Blue-Grey `#D8DFE1`, Muted Blue-Grey `#7B9EAB`. Hero gradient green→petrol.
- **Font:** Changa (weights 400/600/700/800), self-hosted.
- **Language:** English, LTR. Values (phone/email) rendered `dir="ltr"`.
- All work happens on branch `feat/employee-cards` (already checked out).

---

### Task 1: Shared pure helpers + Vitest harness

**Files:**
- Create: `src/lib/employees.js`
- Test: `src/lib/employees.test.js`
- Modify: `package.json` (add `vitest` devDependency + `test` script)

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `slugify(name: string): string`
  - `stripHonorific(name: string): string`
  - `normalizePhone(raw: string): string` — E.164, e.g. `" 00964 7717458968"` → `"+9647717458968"`
  - `formatPhoneDisplay(e164: string): string` — e.g. `"+9647717458968"` → `"+964 771 745 8968"`
  - `initials(name: string): string` — e.g. `"Dr. Osama Dawud"` → `"OD"`
  - `buildVCard(emp: {name,title,org,phone,email}): string` — full VCARD 3.0 text with CRLF

- [ ] **Step 1: Add Vitest and the test script**

Run: `npm install -D vitest`

Then edit `package.json` `"scripts"` to add:
```json
"test": "vitest run"
```

- [ ] **Step 2: Write the failing tests**

Create `src/lib/employees.test.js`:
```js
import { describe, it, expect } from "vitest";
import {
  slugify, stripHonorific, normalizePhone,
  formatPhoneDisplay, initials, buildVCard,
} from "./employees.js";

describe("slugify", () => {
  it("kebab-cases a full name", () => expect(slugify("Hussein Alaa Ali")).toBe("hussein-alaa-ali"));
  it("handles hyphenated surnames", () => expect(slugify("Khlood Ouda Al-Ameri")).toBe("khlood-ouda-al-ameri"));
});

describe("stripHonorific", () => {
  it("drops a leading Dr.", () => expect(stripHonorific("Dr. Osama Dawud")).toBe("Osama Dawud"));
  it("leaves plain names", () => expect(stripHonorific("Maher Zahran")).toBe("Maher Zahran"));
});

describe("normalizePhone", () => {
  it("converts 00 prefix and strips spaces", () => expect(normalizePhone(" 00964 7717458968")).toBe("+9647717458968"));
  it("keeps an existing + number", () => expect(normalizePhone("+962795144133")).toBe("+962795144133"));
});

describe("formatPhoneDisplay", () => {
  it("groups Iraqi numbers 3-3-4", () => expect(formatPhoneDisplay("+9647717458968")).toBe("+964 771 745 8968"));
  it("groups Jordanian numbers", () => expect(formatPhoneDisplay("+962795144133")).toBe("+962 795 144 133"));
  it("returns unknown shapes unchanged", () => expect(formatPhoneDisplay("+15551234")).toBe("+15551234"));
});

describe("initials", () => {
  it("uses the first two words", () => expect(initials("Hussein Alaa Ali")).toBe("HA"));
  it("drops the honorific first", () => expect(initials("Dr. Osama Dawud")).toBe("OD"));
});

describe("buildVCard", () => {
  const v = buildVCard({
    name: "Hussein Alaa Ali", title: "IT PMO – Group Level",
    org: "Al Watania Holding Group", phone: "+9647717458968", email: "h.alaa@x.com",
  });
  it("has the full name", () => expect(v).toContain("FN:Hussein Alaa Ali"));
  it("has the title", () => expect(v).toContain("TITLE:IT PMO – Group Level"));
  it("has a work phone", () => expect(v).toContain("TEL;TYPE=WORK,VOICE:+9647717458968"));
  it("has a work email", () => expect(v).toContain("EMAIL;TYPE=WORK:h.alaa@x.com"));
  it("uses CRLF and ends with END", () => expect(v.endsWith("END:VCARD\r\n")).toBe(true));
});
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `npm test`
Expected: FAIL — `Failed to resolve import "./employees.js"`.

- [ ] **Step 4: Implement the module**

Create `src/lib/employees.js`:
```js
// Pure, dependency-free helpers shared by the data generator, the card
// components, and the vCard endpoint. Framework-agnostic so both Node scripts
// and Astro/Vite can import it, and so the logic stays unit-testable.

const HONORIFIC = /^(dr|mr|mrs|ms|eng|prof)\.?\s+/i;
const KNOWN_CC = /^\+(96[24])(\d+)$/; // Iraq (964) + Jordan (962)

export function stripHonorific(name) {
  return name.replace(HONORIFIC, "").trim();
}

export function slugify(name) {
  return name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function normalizePhone(raw) {
  const d = String(raw).trim().replace(/[\s()\-.]/g, "");
  if (d.startsWith("00")) return "+" + d.slice(2);
  return d; // already "+..." or an unexpected shape — leave it
}

export function formatPhoneDisplay(e164) {
  const m = e164.match(KNOWN_CC);
  if (!m) return e164;
  const [, cc, rest] = m;
  const groups = [];
  for (let i = 0; i < rest.length; ) {
    const size = rest.length - i === 4 ? 4 : 3; // let the tail absorb a 4th digit
    groups.push(rest.slice(i, i + size));
    i += size;
  }
  return `+${cc} ${groups.join(" ")}`;
}

export function initials(name) {
  const words = stripHonorific(name).split(/\s+/).filter(Boolean);
  if (words.length === 0) return "?";
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

const esc = (s) =>
  String(s).replace(/\\/g, "\\\\").replace(/;/g, "\\;").replace(/,/g, "\\,").replace(/\n/g, "\\n");

export function buildVCard({ name, title, org, phone, email }) {
  const lines = [
    "BEGIN:VCARD",
    "VERSION:3.0",
    `N:${esc(name)};;;;`,
    `FN:${esc(name)}`,
    `ORG:${esc(org)}`,
  ];
  if (title) lines.push(`TITLE:${esc(title)}`);
  if (phone) lines.push(`TEL;TYPE=WORK,VOICE:${phone}`);
  if (email) lines.push(`EMAIL;TYPE=WORK:${email}`);
  lines.push("END:VCARD");
  return lines.join("\r\n") + "\r\n";
}
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `npm test`
Expected: PASS (all suites green).

- [ ] **Step 6: Commit**

```bash
git add src/lib/employees.js src/lib/employees.test.js package.json package-lock.json
git commit -m "feat: shared employee helpers (slug, phone, vCard) + vitest"
```

---

### Task 2: CSV → `employees.json` generator

**Files:**
- Create: `scripts/build-employees.mjs`
- Test: `scripts/build-employees.test.mjs`
- Create (generated output): `src/data/employees.json`

**Interfaces:**
- Consumes: `slugify`, `stripHonorific`, `normalizePhone` from `src/lib/employees.js`.
- Produces:
  - `parseEmployeesCsv(csvText: string): Employee[]` where
    `Employee = {slug, name, title, org, email, phone, photo:null}`
  - `src/data/employees.json` — 13-entry array consumed by later tasks.

- [ ] **Step 1: Write the failing test**

Create `scripts/build-employees.test.mjs`:
```js
import { describe, it, expect } from "vitest";
import { parseEmployeesCsv } from "./build-employees.mjs";

const SAMPLE = `Employee Name,Position,Email Account,Phone Number,
Talib Dagher Kadhum,Projecs Engineer,T.dagher@alwatania-holding.com,00964 7732988019,
KhloodOuda Al-Ameri,HR Director,k.Al-Ameri@alwatania-holding.com,00964 7800221313,
Dr. Osama Dawud,CEO,o.Dawud@alwatania-holding.com,00962 795144133,`;

describe("parseEmployeesCsv", () => {
  const rows = parseEmployeesCsv(SAMPLE);
  it("parses every data row", () => expect(rows).toHaveLength(3));
  it("fixes the 'Projecs' typo", () => expect(rows[0].title).toBe("Projects Engineer"));
  it("splits the merged 'KhloodOuda' name", () => expect(rows[1].name).toBe("Khlood Ouda Al-Ameri"));
  it("slugs without the honorific", () => expect(rows[2].slug).toBe("osama-dawud"));
  it("keeps the honorific in the display name", () => expect(rows[2].name).toBe("Dr. Osama Dawud"));
  it("normalizes the phone", () => expect(rows[0].phone).toBe("+9647732988019"));
  it("sets the constant org and null photo", () => {
    expect(rows[0].org).toBe("Al Watania Holding Group");
    expect(rows[0].photo).toBeNull();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm test`
Expected: FAIL — cannot resolve `./build-employees.mjs`.

- [ ] **Step 3: Implement the generator**

Create `scripts/build-employees.mjs`:
```js
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { slugify, stripHonorific, normalizePhone } from "../src/lib/employees.js";

const ORG = "Al Watania Holding Group";

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
      return { slug, name, title, org: ORG, email, phone, photo: null };
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
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `npm test`
Expected: PASS.

- [ ] **Step 5: Generate the real data and sanity-check it**

Run: `node scripts/build-employees.mjs`
Expected: `Wrote 13 employees ...`

Run: `node -e "const e=require('./src/data/employees.json'); console.log(e.length, new Set(e.map(x=>x.slug)).size)"`
Expected: `13 13` (13 rows, 13 unique slugs — no collisions).

- [ ] **Step 6: Commit**

```bash
git add scripts/build-employees.mjs scripts/build-employees.test.mjs src/data/employees.json
git commit -m "feat: generate employees.json from CSV"
```

---

### Task 3: Extract the Watania logo asset

**Files:**
- Create: `scripts/extract_logo.py`
- Create (generated): `public/brand/watania-logo.png`

**Interfaces:**
- Produces: `public/brand/watania-logo.png` — the full-color bilingual lockup, used on a light chip in the hero and on white in the footer/index. (No separate white version: the brand guide sanctions the logo on a light chip over dark backgrounds.)

- [ ] **Step 1: Write the extraction script**

Create `scripts/extract_logo.py`:
```python
"""Extract the clean Al Watania lockup from page 35 of the brand PDF.

Renders the page with poppler (pdftoppm), then auto-trims the white
margin with PIL. One-off; re-run only if the source PDF changes.
Replace public/brand/watania-logo.png with an official SVG/PNG when available.
"""
import subprocess
import tempfile
import os
from PIL import Image, ImageChops

PDF = "watania_visual_identity.pdf"
OUT = "public/brand/watania-logo.png"

with tempfile.TemporaryDirectory() as tmp:
    prefix = os.path.join(tmp, "logo")
    subprocess.run(
        ["pdftoppm", "-png", "-f", "35", "-l", "35", "-r", "300", PDF, prefix],
        check=True,
    )
    src = f"{prefix}-35.png"
    im = Image.open(src).convert("RGB")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bbox = ImageChops.difference(im, bg).getbbox()
    im = im.crop(bbox)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
im.save(OUT)
print(f"Saved {OUT} ({im.width}x{im.height})")
```

- [ ] **Step 2: Run it and verify the asset**

Run: `python3 scripts/extract_logo.py`
Expected: `Saved public/brand/watania-logo.png (WxH)` with a landscape lockup (width > height, width ≳ 800px).

Run: `python3 -c "from PIL import Image; im=Image.open('public/brand/watania-logo.png'); print(im.size); assert im.width>im.height and im.width>600"`
Expected: prints the size, no assertion error.

> If page 35 is not the clean lockup (e.g. the PDF changed), adjust `-f/-l` to the page that shows the full-color logo on white, then re-run.

- [ ] **Step 3: Commit**

```bash
git add scripts/extract_logo.py public/brand/watania-logo.png
git commit -m "feat: extract Al Watania logo from brand PDF"
```

---

### Task 4: Employee layout, styles, card component, and card route

**Files:**
- Create: `src/layouts/PersonBase.astro`
- Create: `src/styles/team.css`
- Create: `src/components/PersonCard.astro`
- Create: `src/pages/e/[slug].astro`
- Modify: `package.json` (add `@fontsource/changa`)

**Interfaces:**
- Consumes: `employees.json` (Task 2); `formatPhoneDisplay`, `initials` from `src/lib/employees.js` (Task 1); `public/brand/watania-logo.png` (Task 3).
- Produces: `PersonBase` (props `{title, description?, image?}`), `PersonCard` (props `{emp}`), and static pages at `/e/<slug>`.

- [ ] **Step 1: Add the Changa font**

Run: `npm install @fontsource/changa`

- [ ] **Step 2: Create the LTR base layout**

Create `src/layouts/PersonBase.astro`:
```astro
---
import "@fontsource/changa/400.css";
import "@fontsource/changa/600.css";
import "@fontsource/changa/700.css";
import "@fontsource/changa/800.css";
import "../styles/team.css";
interface Props { title: string; description?: string; image?: string }
const { title, description = "", image } = Astro.props;
---
<!DOCTYPE html>
<html lang="en" dir="ltr">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    {description && <meta name="description" content={description} />}
    <meta property="og:title" content={title} />
    {description && <meta property="og:description" content={description} />}
    {image && <meta property="og:image" content={image} />}
    <meta name="theme-color" content="#003349" />
  </head>
  <body><slot /></body>
</html>
```

- [ ] **Step 3: Create the base stylesheet**

Create `src/styles/team.css`:
```css
:root {
  --petrol: #003349;
  --green: #6abf4b;
  --lbg: #d8dfe1;
  --mbg: #7b9eab;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Changa", system-ui, -apple-system, sans-serif;
  background: #eef1f3;
  color: var(--petrol);
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 28px 16px;
}
.sr-only {
  position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0;
}
```

- [ ] **Step 4: Create the card component**

Create `src/components/PersonCard.astro`:
```astro
---
import { formatPhoneDisplay, initials } from "../lib/employees.js";
interface Emp {
  slug: string; name: string; title: string; org: string;
  email: string; phone: string; photo: string | null;
}
const { emp } = Astro.props as { emp: Emp };
const base = import.meta.env.BASE_URL.replace(/\/$/, "");
const vcf = `${base}/e/vcards/${emp.slug}.vcf`;

const icons = {
  phone: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></svg>',
  email: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>',
  briefcase: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/></svg>',
  save: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg>',
  go: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>',
};
---
<article class="pcard">
  <header class="pcard__hero">
    <img class="pcard__brand" src={base + "/brand/watania-logo.png"} alt={emp.org}
         onerror="this.style.display='none'" />
    <div class="pcard__avatar">
      {emp.photo
        ? <img src={base + emp.photo} alt={emp.name} />
        : <span class="pcard__initials">{initials(emp.name)}</span>}
    </div>
    <h1 class="pcard__name">{emp.name}</h1>
    <p class="pcard__title">{emp.title}</p>
  </header>

  <nav class="pcard__actions">
    <a class="act" href={`tel:${emp.phone}`}><span class="act__i" set:html={icons.phone} /><span>Call</span></a>
    <a class="act" href={`mailto:${emp.email}`}><span class="act__i" set:html={icons.email} /><span>Email</span></a>
    <a class="act" href={vcf}><span class="act__i" set:html={icons.save} /><span>Save</span></a>
  </nav>

  <div class="pcard__body">
    <a class="row" href={`tel:${emp.phone}`}>
      <span class="row__chip" set:html={icons.phone} />
      <span class="row__text">
        <span class="row__value" dir="ltr">{formatPhoneDisplay(emp.phone)}</span>
        <span class="row__label">Mobile</span>
      </span>
      <span class="row__go" set:html={icons.go} />
    </a>
    <a class="row" href={`mailto:${emp.email}`}>
      <span class="row__chip" set:html={icons.email} />
      <span class="row__text">
        <span class="row__value" dir="ltr">{emp.email}</span>
        <span class="row__label">Email</span>
      </span>
      <span class="row__go" set:html={icons.go} />
    </a>
    <div class="row row--static">
      <span class="row__chip" set:html={icons.briefcase} />
      <span class="row__text">
        <span class="row__value">{emp.org}</span>
        <span class="row__label">{emp.title}</span>
      </span>
    </div>
  </div>
</article>

<style>
  .pcard { width: 100%; max-width: 384px; background: #fff; border-radius: 22px;
    overflow: hidden; box-shadow: 0 12px 44px rgba(0,51,73,.16); }
  .pcard__hero { position: relative; padding: 32px 24px 26px; text-align: center;
    color: #fff; background: linear-gradient(160deg, #6abf4b 0%, #2f8560 42%, #003349 100%); }
  .pcard__brand { position: absolute; top: 14px; left: 14px; height: 30px;
    background: #fff; padding: 5px 8px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,.12); }
  .pcard__avatar { width: 116px; height: 116px; margin: 6px auto 16px; border-radius: 50%;
    background: rgba(255,255,255,.15); border: 3px solid rgba(255,255,255,.9);
    display: grid; place-items: center; overflow: hidden; }
  .pcard__avatar img { width: 100%; height: 100%; object-fit: cover; }
  .pcard__initials { font-size: 42px; font-weight: 800; letter-spacing: 1px; }
  .pcard__name { margin: 0; font-size: 24px; font-weight: 800; line-height: 1.15; }
  .pcard__title { margin: 7px 0 0; font-size: 15px; font-weight: 600; color: #dbe6d6; }
  .pcard__actions { display: grid; grid-template-columns: repeat(3, 1fr); background: #003349; }
  .act { display: flex; flex-direction: column; align-items: center; gap: 6px;
    padding: 15px 4px; color: #fff; text-decoration: none; font-size: 12px; font-weight: 600; }
  .act + .act { border-left: 1px solid rgba(255,255,255,.12); }
  .act__i :global(svg) { width: 20px; height: 20px; }
  .act:active { background: #6abf4b; }
  .pcard__body { padding: 8px 16px 18px; }
  .row { display: flex; align-items: center; gap: 14px; padding: 14px 6px;
    text-decoration: none; color: #003349; border-bottom: 1px solid #eef1f2; }
  .row:last-child { border-bottom: 0; }
  .row--static { cursor: default; }
  .row__chip { flex: 0 0 40px; height: 40px; border-radius: 11px; background: #eaf5e6;
    color: #3f9a2e; display: grid; place-items: center; }
  .row__chip :global(svg) { width: 19px; height: 19px; }
  .row__text { display: flex; flex-direction: column; min-width: 0; flex: 1; }
  .row__value { font-size: 15px; font-weight: 600; overflow: hidden;
    text-overflow: ellipsis; white-space: nowrap; }
  .row__label { font-size: 12px; color: #7b9eab; margin-top: 2px; }
  .row__go { margin-left: auto; color: #c4ccce; }
  .row__go :global(svg) { width: 18px; height: 18px; }
</style>
```

- [ ] **Step 5: Create the card route**

Create `src/pages/e/[slug].astro`:
```astro
---
import PersonBase from "../../layouts/PersonBase.astro";
import PersonCard from "../../components/PersonCard.astro";
import employees from "../../data/employees.json";

export function getStaticPaths() {
  return employees.map((emp) => ({ params: { slug: emp.slug }, props: { emp } }));
}
const { emp } = Astro.props;
const base = import.meta.env.BASE_URL.replace(/\/$/, "");
const image = Astro.site
  ? new URL(base + (emp.photo || "/brand/watania-logo.png"), Astro.site).href
  : undefined;
---
<PersonBase title={emp.name} description={`${emp.name} — ${emp.org}`} image={image}>
  <PersonCard emp={emp} />
</PersonBase>
```

- [ ] **Step 6: Build and verify the card renders**

Run: `npm run build`
Expected: build succeeds; `dist/e/hussein-alaa-ali/index.html` exists.

Run:
```bash
node -e "const h=require('fs').readFileSync('dist/e/hussein-alaa-ali/index.html','utf8'); \
for (const s of ['Hussein Alaa Ali','IT PMO','tel:+9647717458968','mailto:h.alaa@alwatania-holding.com','/e/vcards/hussein-alaa-ali.vcf','+964 771 745 8968']) { \
  if(!h.includes(s)){console.error('MISSING:',s);process.exit(1)} } console.log('card OK')"
```
Expected: `card OK`.

- [ ] **Step 7: Commit**

```bash
git add src/layouts/PersonBase.astro src/styles/team.css src/components/PersonCard.astro src/pages/e/[slug].astro package.json package-lock.json
git commit -m "feat: employee card layout, styles, component, and /e/<slug> route"
```

---

### Task 5: Employee vCard endpoint

**Files:**
- Create: `src/pages/e/vcards/[slug].vcf.ts`

**Interfaces:**
- Consumes: `employees.json` (Task 2); `buildVCard` from `src/lib/employees.js` (Task 1).
- Produces: static `/e/vcards/<slug>.vcf` for every employee.

- [ ] **Step 1: Create the endpoint**

Create `src/pages/e/vcards/[slug].vcf.ts`:
```ts
import type { APIRoute } from "astro";
import employees from "../../../data/employees.json";
import { buildVCard } from "../../../lib/employees.js";

interface Emp {
  slug: string; name: string; title: string; org: string; email: string; phone: string;
}

export function getStaticPaths() {
  return (employees as Emp[]).map((emp) => ({ params: { slug: emp.slug }, props: { emp } }));
}

export const GET: APIRoute = ({ props }) => {
  const emp = props.emp as Emp;
  return new Response(buildVCard(emp), {
    headers: { "Content-Type": "text/vcard; charset=utf-8" },
  });
};
```

- [ ] **Step 2: Build and verify the vCard output**

Run: `npm run build`
Expected: build succeeds; `dist/e/vcards/hussein-alaa-ali.vcf` exists.

Run:
```bash
node -e "const v=require('fs').readFileSync('dist/e/vcards/hussein-alaa-ali.vcf','utf8'); \
for (const s of ['BEGIN:VCARD','FN:Hussein Alaa Ali','ORG:Al Watania Holding Group','TITLE:IT PMO','TEL;TYPE=WORK,VOICE:+9647717458968','EMAIL;TYPE=WORK:h.alaa@alwatania-holding.com','END:VCARD']) { \
  if(!v.includes(s)){console.error('MISSING:',s);process.exit(1)} } console.log('vcard OK')"
```
Expected: `vcard OK`.

- [ ] **Step 3: Commit**

```bash
git add src/pages/e/vcards/[slug].vcf.ts
git commit -m "feat: employee vCard endpoint"
```

---

### Task 6: Team directory index

**Files:**
- Create: `src/pages/e/index.astro`
- Modify: `src/styles/team.css` (append index-grid styles)

**Interfaces:**
- Consumes: `employees.json` (Task 2); `initials` from `src/lib/employees.js` (Task 1); `PersonBase` (Task 4).
- Produces: static page at `/e` listing all employees.

- [ ] **Step 1: Append index styles to `src/styles/team.css`**

Append to `src/styles/team.css`:
```css
/* Team directory (/e) */
.team { width: 100%; max-width: 760px; text-align: center; }
.team__logo { height: 52px; margin: 4px auto 16px; }
.team__heading { font-size: 22px; font-weight: 800; margin: 0 0 18px; }
.team__grid { list-style: none; margin: 0; padding: 0; display: grid; gap: 14px;
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); }
.tcard { display: flex; flex-direction: column; align-items: center; gap: 7px;
  background: #fff; border-radius: 16px; padding: 22px 14px; text-decoration: none;
  color: var(--petrol); box-shadow: 0 6px 20px rgba(0,51,73,.08); }
.tcard__avatar { width: 66px; height: 66px; border-radius: 50%; overflow: hidden;
  background: linear-gradient(160deg, var(--green), var(--petrol)); color: #fff;
  display: grid; place-items: center; font-weight: 800; font-size: 23px; }
.tcard__avatar img { width: 100%; height: 100%; object-fit: cover; }
.tcard__name { font-weight: 700; font-size: 15px; }
.tcard__title { font-size: 12px; color: var(--mbg); }
```

- [ ] **Step 2: Create the index page**

Create `src/pages/e/index.astro`:
```astro
---
import PersonBase from "../../layouts/PersonBase.astro";
import employees from "../../data/employees.json";
import { initials } from "../../lib/employees.js";
const base = import.meta.env.BASE_URL.replace(/\/$/, "");
---
<PersonBase title="Al Watania Holding Group — Team" description="Al Watania Holding Group team directory">
  <section class="team">
    <img class="team__logo" src={base + "/brand/watania-logo.png"} alt="Al Watania Holding Group"
         onerror="this.style.display='none'" />
    <h1 class="team__heading">Our Team</h1>
    <ul class="team__grid">
      {employees.map((e) => (
        <li>
          <a class="tcard" href={`${base}/e/${e.slug}`}>
            <span class="tcard__avatar">
              {e.photo ? <img src={base + e.photo} alt={e.name} /> : <span>{initials(e.name)}</span>}
            </span>
            <span class="tcard__name">{e.name}</span>
            <span class="tcard__title">{e.title}</span>
          </a>
        </li>
      ))}
    </ul>
  </section>
</PersonBase>
```

- [ ] **Step 3: Build and verify the index**

Run: `npm run build`
Expected: build succeeds; `dist/e/index.html` exists.

Run:
```bash
node -e "const h=require('fs').readFileSync('dist/e/index.html','utf8'); \
const n=(h.match(/class=\"tcard\"/g)||[]).length; \
if(n!==13){console.error('expected 13 cards, got',n);process.exit(1)} \
if(!h.includes('Our Team')){console.error('missing heading');process.exit(1)} console.log('index OK', n)"
```
Expected: `index OK 13`.

- [ ] **Step 4: Commit**

```bash
git add src/pages/e/index.astro src/styles/team.css
git commit -m "feat: team directory at /e"
```

---

### Task 7: QR code generation

**Files:**
- Create: `scripts/make-qr.mjs`
- Modify: `package.json` (add `qrcode` devDependency)
- Create (generated): `qrcodes/e/<slug>.png` (13 files)

**Interfaces:**
- Consumes: `employees.json` (Task 2).
- Produces: one QR PNG per employee encoding `${SITE_URL}${BASE_PATH}/e/<slug>`.

- [ ] **Step 1: Add the qrcode library**

Run: `npm install -D qrcode`

- [ ] **Step 2: Write the QR script**

Create `scripts/make-qr.mjs`:
```js
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
```

- [ ] **Step 3: Generate and verify**

Run: `node scripts/make-qr.mjs`
Expected: 13 lines + `Wrote 13 QR codes ...`

Run: `ls qrcodes/e/*.png | wc -l`
Expected: `13`

- [ ] **Step 4: Commit**

```bash
git add scripts/make-qr.mjs qrcodes/e package.json package-lock.json
git commit -m "feat: generate per-employee QR codes"
```

---

### Task 8: Docs + full end-to-end verification

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: everything above.
- Produces: documentation + a green full build proving associations are untouched.

- [ ] **Step 1: Document the employee cards in `README.md`**

Append this section to `README.md`:
```markdown
## Employee cards (Al Watania Holding Group)

Individual staff cards live at `/e/<slug>` (e.g. `/e/hussein-alaa-ali`), with a
team directory at `/e` and a vCard at `/e/vcards/<slug>.vcf`. English, LTR, Changa
font, Watania petrol/green identity. Fully separate from the association cards.

- Source data: `employees_list.csv`
- Regenerate data:  `node scripts/build-employees.mjs`  → `src/data/employees.json`
- Regenerate QR:    `node scripts/make-qr.mjs`           → `qrcodes/e/`
- Extract the logo: `python3 scripts/extract_logo.py`    (one-off; swap in an official SVG if available)
- Unit tests:       `npm test`

Photos are optional: drop `public/team/<slug>.jpg` and set `"photo": "/team/<slug>.jpg"`
in `src/data/employees.json` (the card falls back to initials when `photo` is null).
Slugs are immutable — they are printed in QR codes.
```

- [ ] **Step 2: Run the unit tests**

Run: `npm test`
Expected: PASS (all suites from Tasks 1–2).

- [ ] **Step 3: Full build and end-to-end verification**

Run: `npm run build`
Expected: build succeeds.

Run:
```bash
node -e "const fs=require('fs'); const e=require('./src/data/employees.json'); \
let ok=true; \
for(const x of e){ \
  for(const p of ['dist/e/'+x.slug+'/index.html','dist/e/vcards/'+x.slug+'.vcf']){ \
    if(!fs.existsSync(p)){console.error('MISSING',p);ok=false} } } \
for(const p of ['dist/e/index.html','dist/wim/index.html','dist/vcards/wim.vcf']){ \
  if(!fs.existsSync(p)){console.error('MISSING',p);ok=false} } \
console.log(ok?'ALL OK — 13 cards + 13 vcards + index, associations intact':'FAILURES ABOVE'); \
process.exit(ok?0:1)"
```
Expected: `ALL OK — 13 cards + 13 vcards + index, associations intact`
(The `dist/wim/...` checks prove the association cards still build unchanged.)

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: document employee cards workflow"
```

---

## Self-Review

**Spec coverage:**
- Isolation from associations → Global Constraints + Task 8 verifies `dist/wim` intact. ✓
- `employees.json` data model + cleanup (Projecs, KhloodOuda, Dr., phone) → Task 2. ✓
- Brand colors/gradient/Changa/motifs → Tasks 3 (logo), 4 (layout/card/styles). ✓
- Card UI (hero, avatar/initials, action band Call/Email/Save, contact rows incl. org) → Task 4. ✓
- Directory `/e` → Task 6. ✓
- vCard with TITLE → Tasks 1 (`buildVCard`) + 5. ✓
- QR codes → Task 7. ✓
- `/e/<slug>` namespace, immutable slugs → Global Constraints + Tasks 4/7. ✓
- Logo extraction with SVG-swap note → Task 3. ✓
- Photos optional, added later → Task 4 card logic + Task 8 README. ✓
- Testing/verification (build emits pages/vcards/index; vCard imports fields; deterministic regen) → build checks in Tasks 4/5/6/8; `npm test` in 1/2. ✓

**Placeholder scan:** No TBD/TODO; every code step has complete code. ✓

**Type consistency:** Helper names (`slugify`, `stripHonorific`, `normalizePhone`, `formatPhoneDisplay`, `initials`, `buildVCard`) are defined in Task 1 and used with identical signatures in Tasks 2, 4, 5, 6. `emp` prop shape is consistent across `PersonCard`, `[slug].astro`, `[slug].vcf.ts`. Import path depths verified (`../lib` from components, `../../data` from `pages/e`, `../../../data` from `pages/e/vcards`). ✓

**Note on frontend polish:** Task 4 ships a complete, on-brand first cut. Visual refinement (spacing, gradient, chevron pattern overlay) can be iterated during execution with the frontend-design skill and a live browser preview — the structure, data, and links are all locked by the build checks.
