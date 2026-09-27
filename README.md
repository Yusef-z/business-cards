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
Set the real domain via the `SITE_URL` environment variable in your host (Netlify/Cloudflare Pages),
or by editing `site` in `astro.config.mjs`.

## Employee cards (tenants)

Each company with staff cards is a **tenant**: `tenants/<id>/` holds its identity
(`tenant.json`: URL prefix, org, colours, asset paths), its source `employees.csv`,
raw `photos/`, and the generated `employees.json`. Tenants share a **design** from
`src/designs/<design>/` (Layout, Card, styles); a tenant with a wholly different look
gets its own design folder. Routes live in `src/pages/<prefix>/` (three thin files).

| tenant    | prefix | design  | public assets | example                     |
|-----------|--------|---------|---------------|-----------------------------|
| `watania` | `/e`   | classic | `public/e/`, `public/team/` | `/e/hussein-alaa-ali`  |
| `alawees` | `/a`   | classic | `public/a/`   | `/a/safaa-shghaty-alazaidy` |

Cards are English, LTR, Changa font. Every card has a directory at `/<prefix>` and a
vCard at `/<prefix>/vcards/<slug>.vcf`. Slugs are immutable — they are printed in QR codes.

Regeneration, per tenant (default `watania`; scripts need Python with
`opencv-python pillow "qrcode[pil]" fonttools`):

    python3 scripts/crop_photos.py alawees      # tenants/alawees/photos/<slug>.<ext> -> public/a/team/<slug>.jpg (face-centred)
    node scripts/build-employees.mjs alawees    # employees.csv -> employees.json (auto-attaches photos)
    python3 scripts/make_og.py alawees          # social-preview card -> public/a/og/<slug>.png
    python3 scripts/make_qr.py alawees          # branded QR -> qrcodes/a/<slug>.png
    npm test

Photos are optional; the card falls back to initials. The CSV has an optional fifth
column for a second phone number.

**Adding a tenant:** copy `tenants/alawees/` and edit `tenant.json`; add `logo.png`,
`banner-bg.png` (and optionally `bottom-bg.png`) under the `assets` folder, and either
supply `logo-white.png` or derive a pixel-aligned one with
`python3 scripts/make_splash_logo.py <id>` (needed for the fill-style splash); copy `src/pages/a/` to `src/pages/<prefix>/` and point its imports at the new
tenant; add a `.tenant-<id>` splash block in `src/designs/classic/styles.css`.
