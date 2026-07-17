# scripts/

- `extract.py` — regenerates `src/data/associations.json` from `دليل الجمعيات.xlsx`. Re-runnable; edits to source data or the `OVERRIDES` map flow through here.
- `check_data.py` — validates the committed JSON (run in CI / before build).
- `crop_logos.py` — crops association logos from the source PDF into `public/logos/`.
