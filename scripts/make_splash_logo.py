"""Derive a pixel-aligned white "unfilled" mark from a tenant's colour logo.

The splash stacks the two and wipes the colour version in from the bottom, so
they must share one canvas exactly — an independently drawn white SVG never
lines up. Produces a solid white mark: the coloured fills become opaque white
and the logo's light strokes (calligraphy, outline, accents) become cut-outs
so the splash background shows through — a blank shape the colour then fills.

Usage: python3 scripts/make_splash_logo.py <tenant-id>   (writes <assets>/logo-white.png)
"""
import os

from PIL import Image

import tenant as tenant_mod

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LO, HI = 0.55, 0.85  # luminance ramp: below LO → opaque white, above HI → transparent


def main() -> None:
    t = tenant_mod.load()
    assets = os.path.join(ROOT, "public", t["assets"].lstrip("/"))
    src = Image.open(os.path.join(assets, "logo.png")).convert("RGBA")
    lum = src.convert("L")
    alpha = src.split()[3]
    out_a = Image.eval(lum, lambda v: 0).convert("L")
    la, aa = lum.load(), alpha.load()
    oa = out_a.load()
    for y in range(src.height):
        for x in range(src.width):
            l = la[x, y] / 255
            k = min(1.0, max(0.0, (l - LO) / (HI - LO)))
            oa[x, y] = round(aa[x, y] * (1 - k))
    out = Image.new("RGBA", src.size, (255, 255, 255, 0))
    out.putalpha(out_a)
    path = os.path.join(assets, "logo-white.png")
    out.save(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
