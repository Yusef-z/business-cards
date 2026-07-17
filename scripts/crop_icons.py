#!/usr/bin/env python3
"""Derive an icon-only mark for each association from its full logo lockup.

The header shows the icon + the association name as text, so the icon must be
just the emblem (no baked-in name). Most lockups stack the icon above the name,
so the icon is the top content band; a few are horizontal or offset and use an
explicit region override. Output is centered on a square purple canvas that
matches the card hero, so it blends seamlessly. Requires Pillow.
Run after crop_logos.py (reads public/logos, writes public/icons).
"""
import subprocess
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "public" / "logos"
OUT = ROOT / "public" / "icons"
PURPLE = (46, 35, 80)      # #2e2350, matches the card hero
THR = 120                  # white-artwork threshold
SIZE = 400

# Lockups where the icon is not the clean top band: region (x0,y0,x1,y1) in
# fractions of the 600x600 lockup to look inside before trimming to content.
REGION_OVERRIDE = {
    "slamatc": (0.66, 0.32, 0.91, 0.67),  # shield emblem, center-right
    "sidam":   (0.45, 0.30, 0.91, 0.64),  # SIDAM wordmark, right
    "ela":     (0.52, 0.06, 0.94, 0.47),  # palm burst, top-right
}

SLUGS = [
    "wim", "mining", "datem", "pmg", "amasca", "iia", "exporters", "saudiscp",
    "slamatc", "pia", "industrialfuture", "mdma", "sidam", "chemical", "tahfez",
    "food", "aircraft", "jba", "bma", "fma", "mema", "ela",
]


def content_box(gray):
    px = gray.load()
    w, h = gray.size
    rows = [y for y in range(h) if sum(1 for x in range(0, w, 2) if px[x, y] >= THR) >= 2]
    cols = [x for x in range(w) if sum(1 for y in range(0, h, 2) if px[x, y] >= THR) >= 2]
    if not rows or not cols:
        return None
    return min(cols), min(rows), max(cols), max(rows)


def top_band(gray):
    """Top content band (icon) for a stacked lockup: first ink run from the top,
    ending at the first vertical gap tall enough to separate icon from name."""
    px = gray.load()
    w, h = gray.size
    rows = [sum(1 for x in range(0, w, 3) if px[x, y] >= THR) for y in range(h)]
    mx = max(rows) or 1
    t = max(2, mx * 0.05)
    y = 0
    while y < h and rows[y] < t:
        y += 1
    top = y
    gap = 0
    end = top
    while y < h:
        if rows[y] >= t:
            end = y
            gap = 0
        else:
            gap += 1
            if gap >= 16 and end > top:
                break
        y += 1
    return top, end


def square(region):
    box = content_box(region.convert("L"))
    if box:
        l, t, r, b = box
        region = region.crop((l, t, r + 1, b + 1))
    cw, ch = region.size
    pad = round(max(cw, ch) * 0.12) + 8
    side = max(cw, ch) + 2 * pad
    canvas = Image.new("RGB", (side, side), PURPLE)
    canvas.paste(region, ((side - cw) // 2, (side - ch) // 2))
    return canvas.resize((SIZE, SIZE), Image.LANCZOS)


def make_icon(slug):
    im = Image.open(SRC / f"{slug}.png").convert("RGB")
    w, h = im.size
    if slug in REGION_OVERRIDE:
        x0, y0, x1, y1 = REGION_OVERRIDE[slug]
        region = im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
    else:
        top, end = top_band(im.convert("L"))
        pad = 10
        region = im.crop((0, max(0, top - pad), w, min(h, end + pad)))
    square(region).save(OUT / f"{slug}.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for slug in SLUGS:
        make_icon(slug)
    print(f"wrote {len(SLUGS)} icons to {OUT}")


if __name__ == "__main__":
    sys.exit(main())
