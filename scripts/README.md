# scripts/

- `extract.py` — regenerates `src/data/associations.json` from `دليل الجمعيات.xlsx`. Re-runnable; edits to source data or the `OVERRIDES` map flow through here.
- `check_data.py` — validates the committed JSON (run in CI / before build).
- `crop_logos.py` — crops the full logo lockups (icon + name) from the source PDF into `public/logos/`. Used for social share (Open Graph) images.
- `crop_icons.py` — derives an icon-only mark for each association from `public/logos/` into `public/icons/`. Used in the card header beside the name text. Run after `crop_logos.py`.
