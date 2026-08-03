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

## Employee cards (Al Watania Holding Group)

Individual staff cards live at `/e/<slug>` (e.g. `/e/hussein-alaa-ali`), with a
team directory at `/e` and a vCard at `/e/vcards/<slug>.vcf`. English, LTR, Changa
font, Watania petrol/green identity. Fully separate from the association cards.

- Source data: `employees_list.csv`
- Crop photos:      `python3 scripts/crop_photos.py`      `photos/<slug>.<ext>` → `public/team/<slug>.jpg` (face-centred; needs `pip install opencv-python pillow`)
- Regenerate data:  `node scripts/build-employees.mjs`  → `src/data/employees.json` (auto-attaches any `public/team/<slug>.*`)
- Regenerate QR:    `python3 scripts/make_qr.py`         → `qrcodes/e/` (branded, logo-centered; needs `pip install "qrcode[pil]"`)
- Extract the logo: `python3 scripts/extract_logo.py`    (one-off; swap in an official SVG if available)
- Unit tests:       `npm test`

Photos are optional. To add one: drop the raw headshot in `photos/<slug>.<ext>`,
run `crop_photos.py` (face-centres it into `public/team/<slug>.jpg`), then re-run
`build-employees.mjs`. The card falls back to initials when a person has no photo.
Slugs are immutable — they are printed in QR codes.
