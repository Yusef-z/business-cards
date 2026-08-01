"""Extract the clean Al Watania lockup from page 35 of the brand PDF.

Renders the page with poppler (pdftoppm), then auto-trims the white
margin with PIL. One-off; re-run only if the source PDF changes.
Replace public/brand/watania-logo.png with an official SVG/PNG when available.
"""
import subprocess
import tempfile
import os
from PIL import Image, ImageChops

PDF = "watania_visual_identity.pdf"
OUT = "public/brand/watania-logo.png"

with tempfile.TemporaryDirectory() as tmp:
    prefix = os.path.join(tmp, "logo")
    subprocess.run(
        ["pdftoppm", "-png", "-f", "35", "-l", "35", "-r", "300", PDF, prefix],
        check=True,
    )
    src = f"{prefix}-35.png"
    im = Image.open(src).convert("RGB")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bbox = ImageChops.difference(im, bg).getbbox()
    im = im.crop(bbox)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
im.save(OUT)
print(f"Saved {OUT} ({im.width}x{im.height})")
