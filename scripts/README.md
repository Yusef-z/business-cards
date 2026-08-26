# scripts/

- `extract.py` — regenerates `src/data/associations.json` from `دليل الجمعيات.xlsx`. Re-runnable; edits to source data or the `OVERRIDES` map flow through here.
- `check_data.py` — validates the committed JSON (run in CI / before build).
- `crop_logos.py` — crops the full logo lockups (icon + name) from the source PDF into `public/logos/`. Used for social share (Open Graph) images.
- `crop_icons.py` — derives an icon-only mark for each association from `public/logos/` into `public/icons/`. Used in the card header beside the name text. Run after `crop_logos.py`.

## Employee cards (`/e/<slug>`)

Regeneration order after adding/changing an employee or photo:

1. drop the raw photo at `photos/<slug>.<ext>` (keeps the original)
2. `crop_photos.py` — YuNet face-centred square 600×600 crop → `public/team/<slug>.jpg` (used on the card)
3. `build-employees.mjs` — parse `employees_list.csv` → `src/data/employees.json`, auto-attaching any `public/team/<slug>.jpg`
4. `make_og.py` — 1200×630 brand social-preview card (avatar + name + position) → `public/e/og/<slug>.png` (the page's `og:image`)
5. `make_qr.py` — branded QR to the live card → `qrcodes/e/<slug>.png`
