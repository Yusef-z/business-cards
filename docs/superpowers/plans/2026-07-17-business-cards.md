# Association Business Cards — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a static Astro site that serves a digital business card for each of 22 Saudi industrial-sector associations at a readable slug URL (e.g. `/wim`), deployable free.

**Architecture:** One `Card.astro` component renders from a committed `src/data/associations.json`. A dynamic `[slug].astro` route uses `getStaticPaths` to pre-render 22 static card pages; a static endpoint pre-renders one downloadable vCard per association. Logos are cropped from the source PDF; the card falls back to the styled Arabic name when a logo is missing, so the site is never blocked on logo quality.

**Tech Stack:** Astro 5 (static output, zero client JS), Node 22, `@fontsource/ibm-plex-sans-arabic`, Python 3 stdlib (data extraction — no third-party libs), Pillow + poppler (`pdftoppm`) for logo cropping.

## Global Constraints

- **Language/direction:** Arabic only. Every page is `<html lang="ar" dir="rtl">`.
- **Static output:** `astro build` must produce plain HTML/CSS in `dist/`. No server, no runtime JavaScript required to view a card.
- **Slugs are immutable:** the 22 slugs below are printed into QR codes; never rename one after publish.
- **Phone format:** all phones stored as E.164 `+9665XXXXXXXX`.
- **Missing fields are omitted:** a card/vCard renders only the fields present in its JSON record. Only `slug`, `name`, `logo` are guaranteed present.
- **Node 22, Astro 5.** Free static host (Cloudflare Pages or Netlify) — never cPanel.
- **Canonical slug list (immutable):** `wim, mining, datem, pmg, amasca, iia, exporters, saudiscp, slamatc, pia, industrialfuture, mdma, sidam, chemical, tahfez, food, aircraft, jba, bma, fma, mema, ela`.

---

### Task 1: Astro project scaffold + static build config

**Files:**
- Create: `package.json`
- Create: `astro.config.mjs`
- Create: `tsconfig.json`
- Create: `.gitignore`
- Create: `src/pages/index.astro` (placeholder, replaced in Task 7)

**Interfaces:**
- Produces: a buildable Astro project. `npm run build` emits `dist/`. Later tasks add pages under `src/pages/`.

- [ ] **Step 1: Create `package.json`**

```json
{
  "name": "association-cards",
  "type": "module",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "astro dev",
    "build": "astro build",
    "preview": "astro preview"
  },
  "dependencies": {
    "astro": "^5.0.0",
    "@fontsource/ibm-plex-sans-arabic": "^5.0.0"
  }
}
```

- [ ] **Step 2: Create `astro.config.mjs`**

```js
import { defineConfig } from 'astro/config';

export default defineConfig({
  output: 'static',
  build: { format: 'directory' },
  trailingSlash: 'ignore',
});
```

- [ ] **Step 3: Create `tsconfig.json`**

```json
{ "extends": "astro/tsconfigs/strict" }
```

- [ ] **Step 4: Create `.gitignore`**

```
node_modules/
dist/
.astro/
/tmp/
*.log
```

- [ ] **Step 5: Create a placeholder `src/pages/index.astro`** (replaced in Task 7)

```astro
---
---
<!DOCTYPE html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8" /><title>نتاج</title></head>
<body></body></html>
```

- [ ] **Step 6: Install and build**

Run: `npm install && npm run build`
Expected: build completes, `dist/index.html` exists.

- [ ] **Step 7: Commit**

```bash
git add package.json package-lock.json astro.config.mjs tsconfig.json .gitignore src/pages/index.astro
git commit -m "chore: scaffold Astro static project"
```

---

### Task 2: Data extraction script → `src/data/associations.json`

Reads the source Excel by cell reference (sparse-cell safe) using only the Python standard library, applies cleaning rules, and writes the committed data file. The extraction was validated during design; the override map below fixes the four cells that hold descriptive text instead of clean values.

**Files:**
- Create: `scripts/extract.py`
- Create (generated, committed): `src/data/associations.json`
- Create: `scripts/README.md`

**Interfaces:**
- Produces: `src/data/associations.json` — a JSON array of 22 records. Record shape:
  `{ slug: string, name: string, phone?: "+9665XXXXXXXX", email?: string, website?: "https://…", linkedin?: string, x?: string, logo: "/logos/<slug>.png" }`.
  Consumed by Tasks 3, 4, 5, 6.

- [ ] **Step 1: Write `scripts/extract.py`**

```python
#!/usr/bin/env python3
"""Extract association data from the source Excel into src/data/associations.json.
Pure stdlib (zipfile + ElementTree) — no third-party deps. Re-runnable."""
import zipfile, re, json, sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
XLSX = ROOT / "دليل الجمعيات.xlsx"
OUT = ROOT / "src" / "data" / "associations.json"
M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

# Row (in sheet «قاعدة بيانات الجمعيات», sheet3) -> immutable slug. Rows 3..24.
ROW_SLUG = {
    3: "wim", 4: "mining", 5: "datem", 6: "pmg", 7: "amasca", 8: "iia",
    9: "exporters", 10: "saudiscp", 11: "slamatc", 12: "pia",
    13: "industrialfuture", 14: "mdma", 15: "sidam", 16: "chemical",
    17: "tahfez", 18: "food", 19: "aircraft", 20: "jba", 21: "bma",
    22: "fma", 23: "mema", 24: "ela",
}

# Cells that hold descriptive text / wrong or corrupted values.
# Verified against each association's email + website domain during design.
OVERRIDES = {
    "chemical": {"x": "https://x.com/chemicalsa_sa"},   # cell: "(1) … (@chemicalsa_sa) / X"
    "fma": {"linkedin": None},                           # cell: a page-title string, no URL
    "mema": {"linkedin": None, "website": "https://www.mema.org.sa"},  # LI was a /posts/ link
    "mdma": {"website": "https://www.mdma.org.sa"},      # cell held Arabic text
}

def load(sheet_path):
    z = zipfile.ZipFile(XLSX)
    ss = ET.fromstring(z.read("xl/sharedStrings.xml"))
    strings = ["".join(t.text or "" for t in si.iter(M + "t")) for si in ss]
    sh = ET.fromstring(z.read(sheet_path))
    cells = {}
    for c in sh.iter(M + "c"):
        ref = c.get("r")
        if not ref:
            continue
        col = re.match(r"[A-Z]+", ref).group()
        row = int(re.search(r"\d+", ref).group())
        v = c.find(M + "v")
        val = v.text if v is not None else ""
        if c.get("t") == "s" and val != "":
            val = strings[int(val)]
        cells.setdefault(row, {})[col] = val
    return cells

def is_url(s):
    return bool(s) and s.strip() not in ("--", "") and re.match(r"https?://|www\.", s.strip())

def norm_url(s):
    s = s.strip()
    return s if s.startswith("http") else "https://" + s

def clean_email(e):
    e = (e or "").strip().lower().replace("_x0001_", "-")
    return e or None

def clean_phone(p):
    d = re.sub(r"\D", "", p or "")
    if not d:
        return None
    if d.startswith("0"):
        d = d[1:]
    return "+966" + d

def build():
    cells = load("xl/worksheets/sheet3.xml")
    out = []
    for row in range(3, 25):
        r = cells[row]
        slug = ROW_SLUG[row]
        ov = OVERRIDES.get(slug, {})
        rec = {"slug": slug, "name": r.get("A", "").strip()}
        ph = clean_phone(r.get("H", ""))
        if ph:
            rec["phone"] = ph
        em = ov["email"] if "email" in ov else clean_email(r.get("G", ""))
        if em:
            rec["email"] = em
        web = ov["website"] if "website" in ov else (norm_url(r["F"]) if is_url(r.get("F", "")) else None)
        if web:
            rec["website"] = web
        li = ov["linkedin"] if "linkedin" in ov else (r["B"].strip() if is_url(r.get("B", "")) else None)
        if li:
            rec["linkedin"] = li
        x = ov["x"] if "x" in ov else (r["D"].strip() if is_url(r.get("D", "")) else None)
        if x:
            rec["x"] = x
        rec["logo"] = f"/logos/{slug}.png"
        out.append(rec)
    return out

def main():
    data = build()
    assert len(data) == 22, f"expected 22 records, got {len(data)}"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(data)} records to {OUT}")

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run extraction**

Run: `python3 scripts/extract.py`
Expected: `wrote 22 records to .../src/data/associations.json`

- [ ] **Step 3: Verify known cleaned values with a quick check**

Run:
```bash
python3 - <<'PY'
import json
d = {r["slug"]: r for r in json.load(open("src/data/associations.json"))}
assert len(d) == 22
assert d["pmg"]["email"] == "info@pmg-sa.org"          # _x0001_ + lowercase fix
assert d["food"]["email"] == "info@food-ma.org"        # _x0001_ fix
assert d["chemical"]["x"] == "https://x.com/chemicalsa_sa"   # recovered handle
assert d["mdma"]["website"] == "https://www.mdma.org.sa"     # Arabic-text cell fixed
assert d["wim"]["phone"] == "+966594313045"            # E.164
assert "linkedin" not in d["fma"] and "linkedin" not in d["mema"]  # unusable cells omitted
assert "phone" not in d["mining"]                      # genuinely blank in source
print("OK")
PY
```
Expected: `OK`

- [ ] **Step 4: Write `scripts/README.md`**

```markdown
# scripts/

- `extract.py` — regenerates `src/data/associations.json` from `دليل الجمعيات.xlsx`. Re-runnable; edits to source data or the `OVERRIDES` map flow through here.
- `check_data.py` — validates the committed JSON (run in CI / before build).
- `crop_logos.py` — crops association logos from the source PDF into `public/logos/`.
```

- [ ] **Step 5: Commit**

```bash
git add scripts/extract.py scripts/README.md src/data/associations.json
git commit -m "feat: extract association data to associations.json"
```

---

### Task 3: Data validation script

A guard that fails loudly on malformed data, so a bad edit to the JSON (or a future re-extraction) can't silently ship a broken card.

**Files:**
- Create: `scripts/check_data.py`

**Interfaces:**
- Consumes: `src/data/associations.json` (Task 2).
- Produces: exit code 0 on valid data, non-zero with a message on the first violation.

- [ ] **Step 1: Write the failing test — a temporary broken record**

Run:
```bash
python3 - <<'PY'
import json, subprocess, tempfile, os, shutil
shutil.copy("src/data/associations.json", "/tmp/assoc.bak")
d = json.load(open("src/data/associations.json"))
d[0]["phone"] = "0594313045"   # not E.164 -> must be rejected
json.dump(d, open("src/data/associations.json", "w"), ensure_ascii=False, indent=2)
rc = subprocess.run(["python3", "scripts/check_data.py"]).returncode
shutil.copy("/tmp/assoc.bak", "src/data/associations.json")
assert rc != 0, "check_data should have FAILED on a non-E.164 phone"
print("correctly failed")
PY
```
Expected: this prints `correctly failed` — but only *after* Step 2 exists. Run it now and expect an error (`check_data.py` missing). That is the failing state.

- [ ] **Step 2: Write `scripts/check_data.py`**

```python
#!/usr/bin/env python3
"""Validate src/data/associations.json. Exit non-zero on the first violation."""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data" / "associations.json"
LOGO_DIR = ROOT / "public" / "logos"

SLUG_RE = re.compile(r"^[a-z0-9]+$")
PHONE_RE = re.compile(r"^\+9665\d{8}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

EXPECTED_SLUGS = {
    "wim", "mining", "datem", "pmg", "amasca", "iia", "exporters", "saudiscp",
    "slamatc", "pia", "industrialfuture", "mdma", "sidam", "chemical", "tahfez",
    "food", "aircraft", "jba", "bma", "fma", "mema", "ela",
}

def fail(msg):
    print(f"check_data: FAIL — {msg}", file=sys.stderr)
    sys.exit(1)

def main(check_logos=False):
    data = json.loads(DATA.read_text(encoding="utf-8"))
    if len(data) != 22:
        fail(f"expected 22 records, got {len(data)}")
    slugs = [r["slug"] for r in data]
    if len(set(slugs)) != 22:
        fail("duplicate slug(s)")
    if set(slugs) != EXPECTED_SLUGS:
        fail(f"slug set mismatch: {set(slugs) ^ EXPECTED_SLUGS}")
    for r in data:
        s = r["slug"]
        if not SLUG_RE.match(s):
            fail(f"{s}: bad slug format")
        if not r.get("name", "").strip():
            fail(f"{s}: empty name")
        if r.get("logo") != f"/logos/{s}.png":
            fail(f"{s}: logo path mismatch")
        if "phone" in r and not PHONE_RE.match(r["phone"]):
            fail(f"{s}: phone not E.164 (+9665XXXXXXXX): {r['phone']}")
        if "email" in r and not EMAIL_RE.match(r["email"]):
            fail(f"{s}: bad email: {r['email']}")
        for k in ("website", "linkedin", "x"):
            if k in r and not r[k].startswith("https://"):
                fail(f"{s}: {k} must start with https:// : {r[k]}")
        if check_logos and not (LOGO_DIR / f"{s}.png").exists():
            fail(f"{s}: missing logo file public/logos/{s}.png")
    print(f"check_data: OK — 22 records valid" + (" (logos present)" if check_logos else ""))

if __name__ == "__main__":
    main(check_logos="--logos" in sys.argv)
```

- [ ] **Step 3: Run it against real data**

Run: `python3 scripts/check_data.py`
Expected: `check_data: OK — 22 records valid`

- [ ] **Step 4: Re-run the Step 1 harness to confirm it now catches the break**

Run the Step 1 snippet again.
Expected: `correctly failed`

- [ ] **Step 5: Commit**

```bash
git add scripts/check_data.py
git commit -m "feat: add associations.json validation script"
```

---

### Task 4: Card component + shared layout + theme

The single presentational unit. Renders logo (or Arabic-name fallback), name, a primary "save contact" button, and one action button per present field. RTL, purple theme matching the deck.

**Files:**
- Create: `src/layouts/Base.astro`
- Create: `src/components/Card.astro`
- Create: `src/styles/global.css`

**Interfaces:**
- Consumes: a single record object from `associations.json` (Task 2) as prop `assoc`.
- Produces: `<Card assoc={record} />`. `Base.astro` exposes props `{ title: string, description?: string, image?: string }` and a default slot.

- [ ] **Step 1: Write `src/styles/global.css`**

```css
:root {
  --bg: #2e2350;
  --bg-2: #3a2d63;
  --card: #ffffff;
  --ink: #241a40;
  --muted: #6b6483;
  --accent: #5b3fbf;
  --accent-ink: #ffffff;
  --line: #ece9f5;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: "IBM Plex Sans Arabic", system-ui, sans-serif;
  background: radial-gradient(120% 120% at 50% 0%, var(--bg-2), var(--bg));
  color: var(--ink);
  min-height: 100dvh;
  display: grid;
  place-items: center;
  padding: 24px;
}
.card {
  width: 100%;
  max-width: 400px;
  background: var(--card);
  border-radius: 24px;
  padding: 32px 24px;
  box-shadow: 0 24px 60px rgba(0,0,0,.28);
  text-align: center;
}
.card__logo {
  width: 104px; height: 104px; margin: 0 auto 16px;
  border-radius: 50%; object-fit: contain; background: #fff;
  border: 1px solid var(--line); display: grid; place-items: center;
  overflow: hidden;
}
.card__logo-fallback {
  font-weight: 700; font-size: 15px; color: var(--accent);
  padding: 8px; line-height: 1.3;
}
.card__name { font-size: 22px; font-weight: 700; margin: 0 0 24px; }
.actions { display: flex; flex-direction: column; gap: 10px; }
.btn {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 14px 16px; border-radius: 14px; text-decoration: none;
  font-size: 16px; font-weight: 600; border: 1px solid var(--line);
  color: var(--ink); background: #fff; transition: background .15s;
}
.btn:hover { background: #f6f4fc; }
.btn--primary { background: var(--accent); color: var(--accent-ink); border-color: var(--accent); }
.btn--primary:hover { background: #4a32a0; }
```

- [ ] **Step 2: Write `src/layouts/Base.astro`**

```astro
---
import "@fontsource/ibm-plex-sans-arabic/400.css";
import "@fontsource/ibm-plex-sans-arabic/600.css";
import "@fontsource/ibm-plex-sans-arabic/700.css";
import "../styles/global.css";
interface Props { title: string; description?: string; image?: string }
const { title, description = "", image } = Astro.props;
---
<!DOCTYPE html>
<html lang="ar" dir="rtl">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    {description && <meta name="description" content={description} />}
    <meta property="og:title" content={title} />
    {description && <meta property="og:description" content={description} />}
    {image && <meta property="og:image" content={image} />}
    <meta name="theme-color" content="#2e2350" />
  </head>
  <body>
    <slot />
  </body>
</html>
```

- [ ] **Step 3: Write `src/components/Card.astro`**

```astro
---
interface Assoc {
  slug: string; name: string; logo: string;
  phone?: string; email?: string; website?: string; linkedin?: string; x?: string;
}
const { assoc } = Astro.props as { assoc: Assoc };
---
<div class="card">
  <div class="card__logo">
    <img
      src={assoc.logo}
      alt={assoc.name}
      width="104" height="104"
      onerror="this.replaceWith(Object.assign(document.createElement('div'),{className:'card__logo-fallback',textContent:this.alt}))"
    />
  </div>
  <h1 class="card__name">{assoc.name}</h1>
  <div class="actions">
    <a class="btn btn--primary" href={`/vcards/${assoc.slug}.vcf`}>حفظ جهة الاتصال</a>
    {assoc.phone && <a class="btn" href={`tel:${assoc.phone}`}>اتصال</a>}
    {assoc.email && <a class="btn" href={`mailto:${assoc.email}`}>البريد الإلكتروني</a>}
    {assoc.website && <a class="btn" href={assoc.website} target="_blank" rel="noopener">الموقع الإلكتروني</a>}
    {assoc.linkedin && <a class="btn" href={assoc.linkedin} target="_blank" rel="noopener">لينكدإن</a>}
    {assoc.x && <a class="btn" href={assoc.x} target="_blank" rel="noopener">إكس</a>}
  </div>
</div>
```

Note: the `onerror` handler is the *only* JavaScript on the site and is purely a progressive-enhancement fallback for a missing logo image — the page is fully readable without it.

- [ ] **Step 4: Commit**

```bash
git add src/layouts/Base.astro src/components/Card.astro src/styles/global.css
git commit -m "feat: add Card component, base layout, and theme"
```

---

### Task 5: Dynamic card route → 22 static pages

**Files:**
- Create: `src/pages/[slug].astro`

**Interfaces:**
- Consumes: `associations.json` (Task 2), `Base.astro` + `Card.astro` (Task 4).
- Produces: `dist/<slug>/index.html` for each of the 22 slugs.

- [ ] **Step 1: Write `src/pages/[slug].astro`**

```astro
---
import Base from "../layouts/Base.astro";
import Card from "../components/Card.astro";
import associations from "../data/associations.json";

export function getStaticPaths() {
  return associations.map((assoc) => ({
    params: { slug: assoc.slug },
    props: { assoc },
  }));
}
const { assoc } = Astro.props;
const origin = "https://example.com"; // replace with the real domain at deploy time
---
<Base
  title={assoc.name}
  description={`البطاقة التعريفية لـ ${assoc.name}`}
  image={`${origin}${assoc.logo}`}
>
  <Card assoc={assoc} />
</Base>
```

- [ ] **Step 2: Build and verify all 22 pages exist**

Run:
```bash
npm run build
python3 - <<'PY'
import json, pathlib
d = json.load(open("src/data/associations.json"))
missing = [r["slug"] for r in d if not pathlib.Path(f"dist/{r['slug']}/index.html").exists()]
assert not missing, f"missing pages: {missing}"
html = pathlib.Path("dist/wim/index.html").read_text(encoding="utf-8")
assert "جمعية المرأة في التعدين" in html
assert "tel:+966594313045" in html
assert "/vcards/wim.vcf" in html
assert 'dir="rtl"' in html
print("22 pages OK")
PY
```
Expected: `22 pages OK`

- [ ] **Step 3: Commit**

```bash
git add src/pages/[slug].astro
git commit -m "feat: generate 22 static card pages via getStaticPaths"
```

---

### Task 6: vCard endpoint → downloadable `.vcf` per association

Static Astro endpoint that pre-renders one vCard file per association at build time. The card's "save contact" button links here.

**Files:**
- Create: `src/pages/vcards/[slug].vcf.ts`

**Interfaces:**
- Consumes: `associations.json` (Task 2).
- Produces: `dist/vcards/<slug>.vcf` (MIME `text/vcard`) for each of the 22 slugs, containing the Arabic name and any present phone/email/website.

- [ ] **Step 1: Write `src/pages/vcards/[slug].vcf.ts`**

```ts
import type { APIRoute } from "astro";
import associations from "../../data/associations.json";

interface Assoc {
  slug: string; name: string;
  phone?: string; email?: string; website?: string;
}

export function getStaticPaths() {
  return (associations as Assoc[]).map((assoc) => ({ params: { slug: assoc.slug } }));
}

export const GET: APIRoute = ({ props }) => {
  const a = props.assoc as Assoc;
  const lines = [
    "BEGIN:VCARD",
    "VERSION:3.0",
    `N:${a.name};;;;`,
    `FN:${a.name}`,
    `ORG:${a.name}`,
  ];
  if (a.phone) lines.push(`TEL;TYPE=WORK,VOICE:${a.phone}`);
  if (a.email) lines.push(`EMAIL;TYPE=WORK:${a.email}`);
  if (a.website) lines.push(`URL:${a.website}`);
  lines.push("END:VCARD");
  return new Response(lines.join("\r\n") + "\r\n", {
    headers: { "Content-Type": "text/vcard; charset=utf-8" },
  });
};
```

Note: `getStaticPaths` must also pass `props` so `GET` receives the record. Update it to:

```ts
export function getStaticPaths() {
  return (associations as Assoc[]).map((assoc) => ({
    params: { slug: assoc.slug },
    props: { assoc },
  }));
}
```

- [ ] **Step 2: Build and verify vCards**

Run:
```bash
npm run build
python3 - <<'PY'
import json, pathlib
d = json.load(open("src/data/associations.json"))
missing = [r["slug"] for r in d if not pathlib.Path(f"dist/vcards/{r['slug']}.vcf").exists()]
assert not missing, f"missing vcards: {missing}"
vcf = pathlib.Path("dist/vcards/wim.vcf").read_text(encoding="utf-8")
assert "FN:جمعية المرأة في التعدين" in vcf
assert "TEL;TYPE=WORK,VOICE:+966594313045" in vcf
assert "EMAIL;TYPE=WORK:info@wim.org.sa" in vcf
mining = pathlib.Path("dist/vcards/mining.vcf").read_text(encoding="utf-8")
assert "TEL" not in mining   # mining has no phone -> line omitted
print("22 vcards OK")
PY
```
Expected: `22 vcards OK`

- [ ] **Step 3: Commit**

```bash
git add src/pages/vcards/[slug].vcf.ts
git commit -m "feat: generate downloadable vCard per association"
```

---

### Task 7: Root page + 404

Root is intentionally minimal (per design: "nothing / redirect later"). 404 is an Arabic not-found page for unknown codes.

**Files:**
- Modify: `src/pages/index.astro` (replace Task 1 placeholder)
- Create: `src/pages/404.astro`

**Interfaces:**
- Consumes: `Base.astro` (Task 4).
- Produces: `dist/index.html`, `dist/404.html`.

- [ ] **Step 1: Replace `src/pages/index.astro`**

```astro
---
import Base from "../layouts/Base.astro";
---
<Base title="نتاج">
  <div class="card" style="max-width:360px">
    <img class="card__logo" src="/logos/_brand.png" alt="نتاج"
      onerror="this.replaceWith(Object.assign(document.createElement('div'),{className:'card__logo-fallback',textContent:'نتاج'}))" />
    <h1 class="card__name" style="margin-bottom:0">الدليل التعريفي للجمعيات</h1>
  </div>
</Base>
```

- [ ] **Step 2: Write `src/pages/404.astro`**

```astro
---
import Base from "../layouts/Base.astro";
---
<Base title="الصفحة غير موجودة">
  <div class="card" style="max-width:360px">
    <h1 class="card__name">الصفحة غير موجودة</h1>
    <p style="color:var(--muted);margin:0">تأكد من صحة الرابط.</p>
  </div>
</Base>
```

- [ ] **Step 3: Build and verify**

Run:
```bash
npm run build
python3 - <<'PY'
import pathlib
assert pathlib.Path("dist/index.html").exists()
assert pathlib.Path("dist/404.html").exists()
assert "الصفحة غير موجودة" in pathlib.Path("dist/404.html").read_text(encoding="utf-8")
print("root + 404 OK")
PY
```
Expected: `root + 404 OK`

- [ ] **Step 4: Commit**

```bash
git add src/pages/index.astro src/pages/404.astro
git commit -m "feat: add minimal root page and Arabic 404"
```

---

### Task 8: Logo extraction from the source PDF

Best-effort, non-blocking (the Card already falls back to the Arabic name). Each of the 22 brand logos is a colored circular badge on the right edge of a row on PDF pages 3–8. This task renders those pages at high resolution and crops each logo. Because the crop boxes are visual, the task ships whatever logos are cleanly cropped and leaves the rest to the fallback; low-quality crops can be swapped later without code changes.

**Files:**
- Create: `scripts/crop_logos.py`
- Create: `scripts/logo_crops.json`
- Create (generated, committed): `public/logos/*.png`

**Interfaces:**
- Consumes: `ملف تعريف الجمعيات (22 جمعية)4.pdf`.
- Produces: `public/logos/<slug>.png` for each slug that has a verified crop box in `logo_crops.json`. Referenced by `associations.json` `logo` field.

- [ ] **Step 1: Install tooling**

Run: `python3 -m pip install --user Pillow`
(`pdftoppm` from poppler is already present — verify with `which pdftoppm`.)

- [ ] **Step 2: Render pages 3–8 to high-resolution PNGs for inspection**

Run:
```bash
mkdir -p /tmp/logopages
pdftoppm -png -r 2000 -f 3 -l 8 "ملف تعريف الجمعيات (22 جمعية)4.pdf" /tmp/logopages/p
ls /tmp/logopages   # p-3.png … p-8.png, each 1166×1654
```

- [ ] **Step 3: Create the crop spec `scripts/logo_crops.json`**

Open each `/tmp/logopages/p-N.png` and, for every association (identified by the Arabic name printed beside its circular logo), record the page number and a normalized bounding box `[x0, y0, x1, y1]` (fractions of width/height, 0–1) around the logo circle. Starting reference — each page has 4 rows; logos sit at the right edge (`x ≈ 0.84–0.98`) centered in each row band (`y ≈ 0.13–0.20`, `0.30–0.37`, `0.49–0.56`, `0.66–0.73`). Adjust per logo by eye. Omit any association whose logo is not cleanly separable (it will use the name fallback). File shape:

```json
{
  "wim":  { "page": 3, "box": [0.83, 0.12, 0.99, 0.22] },
  "mdma": { "page": 4, "box": [0.83, 0.12, 0.99, 0.22] }
}
```

- [ ] **Step 4: Write `scripts/crop_logos.py`**

```python
#!/usr/bin/env python3
"""Crop association logos from rendered PDF pages using scripts/logo_crops.json."""
import json, subprocess, sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "ملف تعريف الجمعيات (22 جمعية)4.pdf"
SPEC = ROOT / "scripts" / "logo_crops.json"
OUT = ROOT / "public" / "logos"
TMP = Path("/tmp/logopages")

def render():
    TMP.mkdir(parents=True, exist_ok=True)
    subprocess.run(["pdftoppm", "-png", "-r", "2000", "-f", "3", "-l", "8",
                    str(PDF), str(TMP / "p")], check=True)

def main():
    render()
    OUT.mkdir(parents=True, exist_ok=True)
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    done = 0
    for slug, s in spec.items():
        img = Image.open(TMP / f"p-{s['page']}.png").convert("RGBA")
        w, h = img.size
        x0, y0, x1, y1 = s["box"]
        crop = img.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
        crop.save(OUT / f"{slug}.png")
        done += 1
    print(f"cropped {done} logos into {OUT}")

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run and visually QA**

Run: `python3 scripts/crop_logos.py`
Then open `public/logos/*.png` and confirm each is the right logo, reasonably centered. Re-tune boxes in `logo_crops.json` and re-run as needed. Delete any crop that looks bad (fallback covers it).

- [ ] **Step 6: Rebuild and run full data check including logo presence for cropped slugs**

Run: `npm run build && python3 scripts/check_data.py`
Expected: `check_data: OK — 22 records valid`
(Run `python3 scripts/check_data.py --logos` only once every slug has a logo file; until then, rely on the fallback.)

- [ ] **Step 7: Commit**

```bash
git add scripts/crop_logos.py scripts/logo_crops.json public/logos
git commit -m "feat: crop association logos from source PDF"
```

---

### Task 9: Deployment config + README

**Files:**
- Create: `netlify.toml`
- Create: `public/_redirects`
- Create: `README.md`

**Interfaces:**
- Consumes: the built `dist/` (all prior tasks).
- Produces: config that makes a free static host build and serve the site with a working 404.

- [ ] **Step 1: Write `netlify.toml`** (Cloudflare Pages uses the same build command/output dir in its dashboard)

```toml
[build]
  command = "npm run build"
  publish = "dist"

[build.environment]
  NODE_VERSION = "22"
```

- [ ] **Step 2: Write `public/_redirects`** (Netlify + Cloudflare Pages both honor this)

```
/* /404.html 404
```

- [ ] **Step 3: Write `README.md`**

```markdown
# Association Business Cards

Static digital business cards for 22 Saudi industrial-sector associations.
Each card lives at `/<slug>` (e.g. `/wim`). Arabic, RTL, zero runtime JS.

## Develop
    npm install
    npm run dev

## Build
    npm run build      # -> dist/

## Data
- Source: `دليل الجمعيات.xlsx`, `ملف تعريف الجمعيات (22 جمعية)4.pdf`
- Regenerate data: `python3 scripts/extract.py`
- Validate:        `python3 scripts/check_data.py`
- Crop logos:      `python3 scripts/crop_logos.py`

To change a card, edit `src/data/associations.json` (or `scripts/extract.py` + re-run) and rebuild.
Slugs are immutable — they are printed in QR codes.

## Deploy (free)
Connect the repo to Cloudflare Pages or Netlify:
build command `npm run build`, output dir `dist`, Node 22.
Set the real domain in `src/pages/[slug].astro` (`origin`) before publishing.
```

- [ ] **Step 4: Final full build + validation**

Run: `npm run build && python3 scripts/check_data.py`
Expected: build succeeds; `check_data: OK — 22 records valid`.

- [ ] **Step 5: Commit**

```bash
git add netlify.toml public/_redirects README.md
git commit -m "chore: add deployment config and README"
```

---

## Self-Review

**Spec coverage:**
- Digital business card content (logo, name, call/email/website/LinkedIn/X, save-contact) → Task 4.
- Readable slugs per association → Global Constraints + Task 2 (`ROW_SLUG`).
- Free static hosting, not cPanel → Task 1 (`output: 'static'`) + Task 9.
- Arabic RTL → `Base.astro` (Task 4), every page.
- Logos cropped from PDF → Task 8, with Card fallback (Task 4) so it is non-blocking.
- Root shows nothing meaningful / redirect later → Task 7.
- Data pipeline (Excel → JSON, cleaning rules, slug table) → Task 2; validation → Task 3.
- vCard save-contact → Task 6.
- Link previews (title/description/OG) → `Base.astro` (Task 4), wired in Task 5.
- Unknown slug → 404 → Task 7 + Task 9 `_redirects`.
- Verification (22 pages, E.164 phones, email/URL format, logo presence, vCard per assoc) → Tasks 3, 5, 6, 8.

**Placeholder scan:** No TBD/TODO. The one intentional deferred item — per-logo crop boxes in `logo_crops.json` — is a visual step with an explicit procedure and a fallback, not a code placeholder. `origin = "https://example.com"` is flagged in Task 5 and README as replace-at-deploy.

**Type consistency:** The `Assoc` record shape (`slug, name, logo` required; `phone, email, website, linkedin, x` optional) is identical across `extract.py`, `check_data.py`, `Card.astro`, `[slug].astro`, and the vCard endpoint. Logo path convention `/logos/<slug>.png` matches between `extract.py`, `check_data.py`, and `crop_logos.py` output.

**Scope:** Single cohesive deliverable (one static site) — no decomposition needed.
