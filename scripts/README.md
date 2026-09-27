# scripts/

- `extract.py` — regenerates `src/data/associations.json` from `دليل الجمعيات.xlsx`. Re-runnable; edits to source data or the `OVERRIDES` map flow through here.
- `check_data.py` — validates the committed JSON (run in CI / before build).
- `crop_logos.py` — crops the full logo lockups (icon + name) from the source PDF into `public/logos/`. Used for social share (Open Graph) images.
- `crop_icons.py` — derives an icon-only mark for each association from `public/logos/` into `public/icons/`. Used in the card header beside the name text. Run after `crop_logos.py`.

## Employee cards (tenants: `/e/<slug>` watania, `/a/<slug>` alawees)

All four scripts take the tenant id as their first argument (default `watania`) and
read `tenants/<id>/tenant.json` via `tenant.py`. Regeneration order after adding or
changing an employee or photo:

1. drop the raw photo at `tenants/<id>/photos/<slug>.<ext>` (keeps the original)
2. `crop_photos.py <id>` — YuNet face-centred square 600×600 crop → `public/<team>/<slug>.jpg` (used on the card)
3. `build-employees.mjs <id>` — parse `tenants/<id>/employees.csv` → `tenants/<id>/employees.json`, auto-attaching any cropped photo
4. `make_og.py <id>` — 820×900 social-preview card (banner, logo, avatar, name, position; colours from `tenant.json`) → `public/<assets>/og/<slug>.png`
5. `make_qr.py <id>` — branded QR (centre logo from `qrLogo`) to the live card → `<qrOut>/<slug>.png`

`make_splash_logo.py <id>` — derives `<assets>/logo-white.png` from `logo.png` (ghosted white, same canvas) so the splash can stack the two and wipe the colour version in from the bottom.
