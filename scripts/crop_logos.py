#!/usr/bin/env python3
"""Crop each association's logo lockup from the source PDF into public/logos/<slug>.png.

The associations' brand marks in the deck are icon + bilingual-name lockups drawn as
white artwork on the deck's purple background (pages 3-8). This script, for each slug
listed in scripts/logo_crops.json, crops that slug's row region, trims to the artwork's
content bounds, and centers it on a square purple canvas that matches the card hero — so
the logo blends seamlessly into the card. Re-runnable; requires Pillow + poppler (pdftoppm).
"""
import json
import subprocess
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "ملف تعريف الجمعيات (22 جمعية)4.pdf"
SPEC = ROOT / "scripts" / "logo_crops.json"
OUT = ROOT / "public" / "logos"
TMP = Path("/tmp/logopages")

PURPLE = (46, 35, 80)   # matches --bg / .card__hero in src/styles/global.css
INK_THRESHOLD = 120     # grayscale value above which a pixel counts as white artwork
SIZE = 600              # output square edge in px


def render():
    """Render deck pages 3-8 at high DPI (the media box is tiny; artwork is high-res)."""
    TMP.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["pdftoppm", "-png", "-r", "2000", "-f", "3", "-l", "8", str(PDF), str(TMP / "p")],
        check=True,
    )


def content_bounds(gray):
    """Return (left, top, right, bottom) of the white artwork within a row crop."""
    px = gray.load()
    w, h = gray.size
    rows = [y for y in range(h) if sum(1 for x in range(0, w, 2) if px[x, y] >= INK_THRESHOLD) >= 2]
    cols = [x for x in range(w) if sum(1 for y in range(0, h, 2) if px[x, y] >= INK_THRESHOLD) >= 2]
    if not rows or not cols:
        return None
    return min(cols), min(rows), max(cols), max(rows)


def crop_one(slug, entry):
    img = Image.open(TMP / f"p-{entry['page']}.png").convert("RGB")
    W, H = img.size
    x0, y0, x1, y1 = entry["box"]
    row = img.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
    bounds = content_bounds(row.convert("L"))
    if bounds is None:
        row.resize((SIZE, SIZE), Image.LANCZOS).save(OUT / f"{slug}.png")
        return
    l, t, r, b = bounds
    padx = int((r - l) * 0.10) + 10
    pady = int((b - t) * 0.12) + 10
    rw, rh = row.size
    content = row.crop((max(0, l - padx), max(0, t - pady), min(rw, r + padx), min(rh, b + pady)))
    cw, ch = content.size
    side = max(cw, ch)
    canvas = Image.new("RGB", (side, side), PURPLE)
    canvas.paste(content, ((side - cw) // 2, (side - ch) // 2))
    canvas.resize((SIZE, SIZE), Image.LANCZOS).save(OUT / f"{slug}.png")


def main():
    render()
    OUT.mkdir(parents=True, exist_ok=True)
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    for slug, entry in spec.items():
        crop_one(slug, entry)
    print(f"cropped {len(spec)} logo lockups into {OUT}")


if __name__ == "__main__":
    sys.exit(main())
