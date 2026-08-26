"""Generate a branded social-preview (Open Graph) image per employee.

WhatsApp / Twitter / LinkedIn crop a shared link's og:image to a wide
~1.91:1 box. Feeding them the tall portrait stretches the person. Instead
we render a fixed 1200x630 card — brand gradient, circular avatar in a white
ring, name + position, and the white Al Watania logo — so the preview always
looks right.

Usage:  python3 scripts/make_og.py
Deps:   pillow, numpy, fonttools   (fonts: node_modules/@fontsource/changa)
Output: public/e/og/<slug>.png
"""
import io
import json
import os

import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMP = os.path.join(ROOT, "src", "data", "employees.json")
TEAM = os.path.join(ROOT, "public", "team")
LOGO = os.path.join(ROOT, "public", "e", "logo-white.png")
OUT_DIR = os.path.join(ROOT, "public", "e", "og")
FONT_DIR = os.path.join(ROOT, "node_modules", "@fontsource", "changa", "files")

W, H = 1200, 630
GREEN = (0x77, 0xB2, 0x5F)   # bottom-left of the gradient
PETROL = (0x03, 0x3E, 0x4F)  # top-right of the gradient
WHITE = (255, 255, 255)
SOFT = (222, 233, 226)       # slightly muted white for the position line


def load_font(weight: int, size: int) -> ImageFont.FreeTypeFont:
    """Load Changa at a weight/size. The package ships .woff only, so
    convert to an in-memory TTF (FreeType/PIL can't read .woff directly)."""
    woff = os.path.join(FONT_DIR, f"changa-latin-{weight}-normal.woff")
    tt = TTFont(woff)
    buf = io.BytesIO()
    tt.flavor = None
    tt.save(buf)
    buf.seek(0)
    return ImageFont.truetype(buf, size)


def gradient_bg() -> Image.Image:
    """Diagonal gradient matching the card: green (bottom-left) -> petrol
    (top-right), i.e. CSS `linear-gradient(to top right, green, petrol)`."""
    xs = np.linspace(0, 1, W)[None, :]
    ys = np.linspace(0, 1, H)[:, None]
    t = ((xs + (1 - ys)) / 2)  # 0 at bottom-left, 1 at top-right
    g = np.stack([GREEN[i] + (PETROL[i] - GREEN[i]) * t for i in range(3)], axis=-1)
    return Image.fromarray(np.broadcast_to(g, (H, W, 3)).astype(np.uint8), "RGB")


HONORIFICS = {"dr", "mr", "mrs", "ms", "eng", "prof"}


def initials(name: str) -> str:
    words = [w for w in name.replace(".", " ").split() if w]
    if words and words[0].lower() in HONORIFICS:
        words = words[1:]  # match the site: strip a leading honorific
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def circular(img: Image.Image, d: int) -> Image.Image:
    """Cover-fit `img` into a d x d circle (transparent outside)."""
    src = img.convert("RGB")
    sw, sh = src.size
    scale = d / min(sw, sh)
    src = src.resize((round(sw * scale), round(sh * scale)), Image.LANCZOS)
    left, top = (src.width - d) // 2, (src.height - d) // 2
    src = src.crop((left, top, left + d, top + d))
    mask = Image.new("L", (d, d), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, d - 1, d - 1], fill=255)
    out = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    out.paste(src, (0, 0), mask)
    return out


def avatar(emp: dict, d: int) -> Image.Image:
    """Photo cropped to a circle, or a soft initials circle when no photo."""
    jpg = os.path.join(TEAM, f"{emp['slug']}.jpg")
    if os.path.exists(jpg):
        return circular(Image.open(jpg), d)
    # No photo: a dark monogram on the (white) avatar circle drawn behind it.
    disc = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    dd = ImageDraw.Draw(disc)
    font = load_font(800, int(d * 0.36))
    txt = initials(emp["name"])
    bb = dd.textbbox((0, 0), txt, font=font)
    dd.text(((d - (bb[2] - bb[0])) / 2 - bb[0], (d - (bb[3] - bb[1])) / 2 - bb[1]),
            txt, font=font, fill=PETROL)
    return disc


def wrap(draw, text, font, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_font(draw, text, weight, start, min_size, max_w):
    """Largest size (<= start, >= min_size) that keeps `text` on one line."""
    size = start
    while size > min_size and draw.textlength(text, font=load_font(weight, size)) > max_w:
        size -= 2
    return load_font(weight, size)


def render(emp: dict, out: str) -> None:
    img = gradient_bg().convert("RGBA")
    draw = ImageDraw.Draw(img)

    # --- Avatar (left), white ring + soft shadow ---
    d = 400
    cx, cy = 90 + d // 2, H // 2
    ring = 12
    r_out = d // 2 + ring
    # Shadow.
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse(
        [cx - r_out, cy - r_out + 16, cx + r_out, cy + r_out + 16], fill=(0, 30, 40, 120))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18)))
    # White ring.
    draw.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], fill=WHITE)
    # Photo.
    av = avatar(emp, d)
    img.alpha_composite(av, (cx - d // 2, cy - d // 2))

    # --- Logo (top-right, white) ---
    logo = Image.open(LOGO).convert("RGBA")
    lw = 250
    logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
    img.alpha_composite(logo, (W - lw - 60, 55))

    # --- Text block (right) ---
    tx = cx + r_out + 70
    max_w = W - tx - 60
    name_font = fit_font(draw, emp["name"], 800, 74, 46, max_w)
    title_font = load_font(700, 38)
    title_lines = wrap(draw, emp["title"], title_font, max_w)

    name_h = draw.textbbox((0, 0), emp["name"], font=name_font)[3]
    line_h = int(title_font.size * 1.28)
    gap = 22
    block_h = name_h + gap + line_h * len(title_lines)
    y = (H - block_h) // 2

    draw.text((tx, y), emp["name"], font=name_font, fill=WHITE)
    y += name_h + gap
    for ln in title_lines:
        draw.text((tx, y), ln, font=title_font, fill=SOFT)
        y += line_h

    img.convert("RGB").save(out, quality=92)


def main() -> None:
    with open(EMP, encoding="utf-8") as f:
        employees = json.load(f)
    os.makedirs(OUT_DIR, exist_ok=True)
    for e in employees:
        out = os.path.join(OUT_DIR, f"{e['slug']}.png")
        render(e, out)
        print(f"{e['slug']:24s} -> public/e/og/{e['slug']}.png")
    print(f"\nWrote {len(employees)} OG images to {OUT_DIR}")


if __name__ == "__main__":
    main()
