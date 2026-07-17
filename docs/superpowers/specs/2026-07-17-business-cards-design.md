# Digital Business Cards for 22 Saudi Industrial Associations — Design

**Date:** 2026-07-17
**Status:** Approved pending user review

## Overview

A static website where each of 22 Saudi industrial-sector associations (جمعيات) has a
digital business card at a readable slug URL, e.g. `example.com/wim`. Visitors see the
association's logo, name, and tappable contact actions (call, email, website, LinkedIn, X),
plus a save-contact (vCard) button. Arabic-only, RTL, mobile-first.

Source data:

- `دليل الجمعيات.xlsx` — sheet «قاعدة بيانات الجمعيات»: name, LinkedIn, X, website, email, phone per association (rows 2–23, all 22 present; some fields missing).
- `ملف تعريف الجمعيات (22 جمعية)4.pdf` — one branded profile page per association; used only as the logo source.

## Decisions made during brainstorming

| Question | Decision |
|---|---|
| Card content | Digital business card only (no full profile) |
| URL codes | Readable slugs derived from each association's own domain/acronym |
| Hosting | Free static hosting (Cloudflare Pages or Netlify) — explicitly not cPanel |
| Language | Arabic only, RTL |
| Logos | Extracted (cropped) from the PDF deck |
| Root URL `/` | Nothing — minimal blank page; redirect target may be added later |
| Stack | Astro static site |

## Data pipeline

A one-time extraction script (Python, kept in `scripts/`) reads the Excel sheet and writes
`src/data/associations.json`. Logos are cropped from high-resolution renders of the PDF
pages into `public/logos/<slug>.png`, followed by a manual visual QA pass.

### JSON shape

```json
{
  "slug": "wim",
  "name": "جمعية المرأة في التعدين",
  "phone": "+966594313045",
  "email": "info@wim.org.sa",
  "website": "https://www.wim.org.sa",
  "linkedin": "https://www.linkedin.com/company/...",
  "x": "https://x.com/sm_wimorg",
  "logo": "/logos/wim.png"
}
```

Missing fields are omitted entirely — a card renders only the buttons for fields it has.

### Cleaning rules

- `_x0001_` XML-escape artifacts in emails: `INFO@pmg_x0001_sa.org` → `info@pmg-sa.org`,
  `info@food_x0001_ma.org` → `info@food-ma.org`. Emails lowercased.
- The website cell for جمعية مصنعي الأجهزة الطبية contains Arabic text, not a URL —
  resolve the real domain (mdma.org.sa) during extraction and verify it responds.
- MEMA website is a deep link to an internal page — normalize to `https://www.mema.org.sa/`.
- Websites without scheme (`www.wim.org.sa`) get `https://` prepended.
- Phones normalized to international format: `050 312 1776` → `+966503121776`.
- `--` and empty cells treated as missing.
- X/LinkedIn share-links (`?s=21` suffixes) kept as-is — they resolve correctly.

### Slug table

| # | Association | Slug |
|---|---|---|
| 1 | جمعية المرأة في التعدين | `wim` |
| 2 | جمعية التعدين | `mining` |
| 3 | جمعية مصنعي التمور | `datem` |
| 4 | جمعية المعادن الثمينة والأحجار الكريمة | `pmg` |
| 5 | جمعية مصنعي السيارات وسلاسل الإمداد | `amasca` |
| 6 | جمعية الابتكار الصناعي | `iia` |
| 7 | جمعية المصدرين الصناعيين | `exporters` |
| 8 | جمعية سلاسل الامداد والمشتريات | `saudiscp` |
| 9 | جمعية سلامتك | `slamatc` |
| 10 | جمعية الصناعات الدوائية | `pia` |
| 11 | جمعية المستقبل الصناعي | `industrialfuture` |
| 12 | جمعية مصنعي الاجهزة الطبية | `mdma` |
| 13 | جمعية التنمية والاستدامة | `sidam` |
| 14 | جمعية مصنعي الكيماويات | `chemical` |
| 15 | جمعية تحفيز الصناعات المحلية | `tahfez` |
| 16 | جمعية مصنعي الاغذية | `food` |
| 17 | جمعية مصنعي الطائرات | `aircraft` |
| 18 | جمعية مصنعي العصائر والمشروبات | `jba` |
| 19 | جمعية مصنعي مواد البناء | `bma` |
| 20 | جمعية مصنعي الأثاث | `fma` |
| 21 | جمعية مصنعي الالات والمعدات | `mema` |
| 22 | جمعية التوطين الهندسي | `ela` |

Slugs are lowercase ASCII, stable once published (they will be printed in QR codes).
Note: `fma` = furniture (fma.org.sa); the food association (food-ma.org) uses `food` to
avoid collision.

## Site architecture

Astro project, fully static output (`astro build` → plain HTML/CSS).

```
src/
  data/associations.json      extracted data (committed)
  pages/
    index.astro               root: minimal blank branded page
    [slug].astro              getStaticPaths over the JSON → 22 static pages
    404.astro                 Arabic "not found" page for unknown codes
  components/Card.astro       the business card component
scripts/
  extract.py                  one-time Excel/PDF extraction (committed for re-runs)
  check_data.py               validation script (see Verification)
public/
  logos/<slug>.png            cropped logos
  vcards/<slug>.vcf           generated at build time from the same JSON
```

- Each card page pre-renders to `/<slug>/index.html`; no client-side JavaScript is
  required to view a card.
- **vCards:** generated at build time (Astro integration hook or a prebuild step) —
  Arabic name (`FN`/`ORG`), phone, email, website. The حفظ جهة الاتصال button links to
  `/vcards/<slug>.vcf`; phones open it directly into "add contact".
- **Link previews:** every page has Arabic `<title>`, meta description, and Open Graph
  tags (name + logo) so WhatsApp/social shares show a proper preview.
- **Unknown slug** → static 404 page in Arabic.

## Card UI

- Mobile-first, RTL (`dir="rtl"` `lang="ar"`), single centered card.
- Layout: logo → association name (Arabic webfont, e.g. IBM Plex Sans Arabic) → primary
  save-contact button → action buttons: اتصال (`tel:`), البريد الإلكتروني (`mailto:`),
  الموقع الإلكتروني, LinkedIn, X.
- Purple visual theme matched to the PDF deck's branding so the cards share the same
  identity.
- Desktop: same card centered on a subtle background — no separate layout.

## Deployment

- Git repo connected to Cloudflare Pages or Netlify (free tier); every push runs
  `astro build` and deploys the static output.
- Free `*.pages.dev` / `*.netlify.app` URL for testing; the custom domain attaches later
  without code changes.

## Verification

- Build produces exactly 22 card pages + root + 404.
- `scripts/check_data.py` validates: slug uniqueness and format, phone in `+966…` E.164
  format, email format, URLs parse with https scheme, referenced logo file exists,
  vCard exists per association after build.
- Visual check of all 22 cards at a phone-sized viewport; logo QA pass (flag any
  low-quality crops for later replacement).

## Out of scope (YAGNI)

- CMS or admin UI — data changes are JSON edits.
- Analytics, QR code generation, English localization, full profile pages — all can be
  added later without rework.
