# Al Watania Employee Cards — Design Spec

**Date:** 2026-08-01
**Status:** Approved (pending spec review)
**Author:** Yusef + Claude

## Goal

Add per-individual digital business cards for Al Watania Holding Group employees to
this existing Astro repo, **without touching** the 22 association cards. Cards follow
the layout of the reference qrco.de card (avatar, name, title, action buttons, contact
list, save-contact) but are elevated to the real Al Watania visual identity.

Source data: `employees_list.csv` (13 employees). Brand source: `watania_visual_identity.pdf`.

## Decisions (locked)

| Question | Decision |
|---|---|
| Language / direction | **English-primary, LTR.** Brand lockup stays bilingual (AR+EN). |
| Location / Directions block | **Omitted** (CSV has no address). |
| Design fidelity | **Premium branded take** — reference layout, real Watania identity. |
| Scope | Card pages + vCards + team index + **QR codes**. |
| URL namespace | **`/e/<slug>`** (short, QR-friendly). Index at `/e`, vCards at `/e/vcards/<slug>.vcf`. |
| Typo fix | Fix `Projecs Engineer → Projects Engineer`; normalize whitespace. |
| Logo | Extract from brand PDF p.35 for now; swap to official SVG if provided. |

## Principle: total isolation from the associations

Nothing powering the association cards changes. The only pre-existing change is the
ngrok host added to `astro.config.mjs` earlier (unrelated to this feature).

**Untouched:** `src/data/associations.json`, `src/components/Card.astro`,
`src/layouts/Base.astro`, `src/styles/global.css`, `src/pages/index.astro`,
`src/pages/[slug].astro`, `src/pages/vcards/[slug].vcf.ts`.

## File layout (new files only)

```
src/
  data/employees.json          generated from employees_list.csv
  components/PersonCard.astro   the employee card UI
  layouts/PersonBase.astro      <html lang="en" dir="ltr">, imports Changa + team styles
  styles/team.css               employee-card styles (keeps global.css untouched)
  pages/e/
    index.astro                 /e  — team directory
    [slug].astro                /e/<slug>  — one card
    vcards/[slug].vcf.ts        /e/vcards/<slug>.vcf
public/
  brand/
    watania-logo.svg            full-color bilingual lockup (footer)
    watania-logo-white.svg      reversed mark for the dark hero
  team/<slug>.jpg               employee photos — added later, optional
scripts/
  build_employees.py            CSV -> src/data/employees.json
  make_qr.py                    QR PNG per employee -> qrcodes/e/<slug>.png
qrcodes/e/<slug>.png            generated QR codes
docs/superpowers/specs/2026-08-01-watania-employee-cards-design.md   this file
```

## Brand system (extracted from the PDF)

### Colors
| Token | Hex | Role |
|---|---|---|
| Petrol Blue | `#003349` | dominant — hero base, primary text |
| Grass Green | `#6ABF4B` | accent — buttons, icons, active states |
| Light Blue-Grey | `#D8DFE1` | light surfaces / dividers |
| Muted Blue-Grey | `#7B9EAB` | secondary text on light |
| (signature gradient) | `#6ABF4B → #003349` | hero background |

Usage roughly follows the brand's 75 / 20 / 5 petrol / green / accent ratio.

### Typography
- **Changa**, self-hosted via `@fontsource/changa` (new dependency).
- Weights: 800 ExtraBold (name / headings), 600 SemiBold (title / labels),
  700 Bold (eyebrows), 400 Regular (values). Import only the weights used.

### Motifs
- Faint chevron / 4-point-star pattern overlay on the hero (from the brand "النقش" pattern).
- Bilingual full-color logo lockup in the footer.

## Data model

`src/data/employees.json` — array of:

```json
{
  "slug": "hussein-alaa-ali",
  "name": "Hussein Alaa Ali",
  "title": "IT PMO – Group Level",
  "org": "Al Watania Holding Group",
  "email": "h.alaa@alwatania-holding.com",
  "phone": "+9647717458968",
  "photo": null
}
```

Rules:
- **slug** — full-name kebab-case (full name, because three employees are named
  "Mustafa"). Immutable once printed in a QR code.
- **phone** — normalized to E.164: strip spaces, leading `00 → +`. Displayed grouped.
  CSV mixes Jordan (`00962`) and Iraq (`00964`); formatter handles both generically.
- **org** — constant `"Al Watania Holding Group"`.
- **photo** — `null` now → initials placeholder. Later set to `/team/<slug>.jpg`;
  the card auto-uses the photo when present.

### Employee mapping (from CSV)

| Slug | Name | Title | Phone (E.164) |
|---|---|---|---|
| osama-dawud | Dr. Osama Dawud | CEO | +962795144133 |
| mustafa-abdulghani | Mustafa Abdulghani | CFO | +9647873931297 |
| khlood-ouda-al-ameri | Khlood Ouda Al-Ameri | HR Director | +9647800221313 |
| reem-manhal-abdulhameed | Reem Manhal Abdulhameed | Deputy HR Director | +9647880984995 |
| jamal-naser-hussein | Jamal Naser Hussein | Internal Control Director | +9647865065090 |
| maher-zahran | Maher Zahran | Internal Audit Director | +9647873931276 |
| jehad-wehbi | Jehad Wehbi | Deputy CFO | +9647814451818 |
| ahmed-qasim-mohammad | Ahmed Qasim Mohammad | Sr. Accountant | +9647893310264 |
| mohamed-essam-elnamas | Mohamed Essam Elnamas | Financial Consultant | +9647855538511 |
| talib-dagher-kadhum | Talib Dagher Kadhum | Projects Engineer | +9647732988019 |
| hussein-alaa-ali | Hussein Alaa Ali | IT PMO – Group Level | +9647717458968 |
| mustafa-saad-hameed | Mustafa Saad Hameed | Internal Audit Officer | +9647857275975 |
| mustafa-hameed-talib | Mustafa Hameed Talib | Internal Control Officer | +9647827125898 |

Data-cleanup notes (applied by `build_employees.py`, called out for review):
- `Dr. Osama Dawud` — honorific kept in display name; slug drops it.
- `KhloodOuda Al-Ameri` — split to `Khlood Ouda Al-Ameri` (merged words in CSV).
- Email `r.Abdulhamed@…` is kept verbatim (real mailbox) even though the name is
  spelled "Abdulhameed".
- Emails displayed as-is; used verbatim in `mailto:` and vCard.

## Card UI (`PersonCard.astro`)

Premium branded, LTR, mobile-first column (~384px max), **zero runtime JS**.

- **Hero** — green→petrol gradient + faint chevron overlay; small white Watania mark
  in a corner; centered circular **avatar** (photo, or initials e.g. "HA" on a brand
  tint when `photo` is null) with a soft ring; **Name** (Changa ExtraBold, white);
  **Title** (SemiBold, light tint).
- **Action band** — three even buttons: **Call · Email · Save contact**
  (Directions omitted). Green/petrol brand styling.
- **Contact list** — icon-chip rows (same interaction pattern as `Card.astro`):
  - Phone (Mobile) → `tel:`
  - Email → `mailto:`
  - Organization (briefcase) → "Al Watania Holding Group", role as subtext.
- **Footer** — bilingual full-color Watania lockup.

Values (phone, email) render `dir="ltr"`.

## Directory (`/e`)

Responsive grid of all 13: avatar, name, title, linking to each card. Brand-styled
header with the Watania lockup.

## vCard (`/e/vcards/<slug>.vcf`)

Reuses the association endpoint pattern (`esc()` + `getStaticPaths`), extended:

```
BEGIN:VCARD
VERSION:3.0
N:<name>;;;;
FN:<name>
ORG:Al Watania Holding Group
TITLE:<title>
TEL;TYPE=WORK,VOICE:<phone>
EMAIL;TYPE=WORK:<email>
END:VCARD
```

Content-Type `text/vcard; charset=utf-8`. Paths respect `BASE_URL`.

## QR codes (`scripts/make_qr.py`)

Generates `qrcodes/e/<slug>.png` for each employee, encoding
`${SITE_URL}${BASE}/e/<slug>`. Slugs are immutable because they are printed in QR
codes (same rule as the associations, per repo README).

## Layout / fonts (`PersonBase.astro`)

Separate from `Base.astro` so the association path stays byte-for-byte identical:
- `<html lang="en" dir="ltr">`
- imports `@fontsource/changa` weights + `src/styles/team.css`
- `theme-color` set to petrol `#003349`
- OG tags: title = employee name, description = "<name> — Al Watania Holding Group",
  image = employee photo when present else the Watania logo.

## Logo dependency

No Al Watania logo exists in the repo. Plan: extract a clean full-color lockup from
brand PDF page 35, plus a white reversed mark for the dark hero, into `public/brand/`.
If an official SVG is provided, use it instead (sharper than an extraction).

## Testing / verification

- `npm run build` succeeds and emits 13 `/e/<slug>` pages, 13 `/e/vcards/<slug>.vcf`,
  and `/e`.
- Spot-check one card: correct name/title/phone/email, working `tel:` / `mailto:` /
  `.vcf` links, initials placeholder avatar renders.
- Import a generated `.vcf` into Contacts and confirm name, title, org, phone, email.
- Re-running `build_employees.py` reproduces `employees.json` deterministically.
- Confirm association cards (`/wim`, `/e` sibling routes) are unaffected.

## Out of scope (later)

- Employee photos (data model ready; drop files into `public/team/`).
- Arabic/bilingual per-person names.
- Any change to the association cards.
