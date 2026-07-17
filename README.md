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
