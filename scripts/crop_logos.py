#!/usr/bin/env python3
"""Crop association logos from rendered PDF pages using scripts/logo_crops.json."""
import json, subprocess, sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "ملف تعريف الجمعيات (22 جمعية)4.pdf"
SPEC = ROOT / "scripts" / "logo_crops.json"
OUT = ROOT / "public" / "logos"
TMP = Path("/tmp/logopages")

def render():
    TMP.mkdir(parents=True, exist_ok=True)
    subprocess.run(["pdftoppm", "-png", "-r", "2000", "-f", "3", "-l", "8",
                    str(PDF), str(TMP / "p")], check=True)

def main():
    render()
    OUT.mkdir(parents=True, exist_ok=True)
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    done = 0
    for slug, s in spec.items():
        img = Image.open(TMP / f"p-{s['page']}.png").convert("RGBA")
        w, h = img.size
        x0, y0, x1, y1 = s["box"]
        crop = img.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
        crop.save(OUT / f"{slug}.png")
        done += 1
    print(f"cropped {done} logos into {OUT}")

if __name__ == "__main__":
    sys.exit(main())
