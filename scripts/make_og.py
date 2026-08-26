"""Generate a branded social-preview (Open Graph) image per employee.

Sharing an employee link on WhatsApp fed the tall portrait as og:image,
which the preview cropped/stretched. Instead we render a fixed vertical card
that mirrors the site's hero — the arch watermark, the colour logo, the photo
in the green ring frame, the navy name and green position — so the preview
always looks like the card itself.

Usage:  python3 scripts/make_og.py
Deps:   pillow, numpy, fonttools   (fonts: node_modules/@fontsource/changa)
Output: public/e/og/<slug>.png  (820x900)
"""
import io
import json
import os

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMP = os.path.join(ROOT, "src", "data", "employees.json")
TEAM = os.path.join(ROOT, "public", "team")
E = os.path.join(ROOT, "public", "e")
OUT_DIR = os.path.join(E, "og")
FONT_DIR = os.path.join(ROOT, "node_modules", "@fontsource", "changa", "files")

W, H = 820, 900
NAVY = (0x00, 0x33, 0x49)     # .ecard__name
GREEN = (0x5C, 0xB5, 0x44)    # .ecard__title
PLACEHOLDER_BG = (0xDF, 0xE6, 0xE8)  # .ecard__photo--ph

# Avatar geometry mirrors the card: ring box D, photo at 94% inside it.
D = 360
PHOTO_RATIO = 0.94
HONORIFICS = {"dr", "mr", "mrs", "ms", "eng", "prof"}


def load_font(weight: int, size: int) -> ImageFont.FreeTypeFont:
    """Load Changa at a weight/size. The package ships .woff only, so
    convert to an in-memory TTF (FreeType/PIL can't read .woff directly)."""
    tt = TTFont(os.path.join(FONT_DIR, f"changa-latin-{weight}-normal.woff"))
    buf = io.BytesIO()
    tt.flavor = None
    tt.save(buf)
    buf.seek(0)
    return ImageFont.truetype(buf, size)


def initials(name: str) -> str:
    words = [w for w in name.replace(".", " ").split() if w]
    if words and words[0].lower() in HONORIFICS:
        words = words[1:]
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def cover(img: Image.Image, w: int, h: int, oy: float = 0.5) -> Image.Image:
    """Resize+crop `img` to fill w x h (object-fit: cover), vertical bias oy."""
    src = img.convert("RGB")
    scale = max(w / src.width, h / src.height)
    src = src.resize((round(src.width * scale), round(src.height * scale)), Image.LANCZOS)
    left = (src.width - w) // 2
    top = int((src.height - h) * oy)
    return src.crop((left, top, left + w, top + h))


def circle(img: Image.Image, d: int) -> Image.Image:
    disc = cover(img, d, d)
    mask = Image.new("L", (d, d), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, d - 1, d - 1], fill=255)
    out = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    out.paste(disc, (0, 0), mask)
    return out


def photo_disc(emp: dict, pd: int) -> Image.Image:
    jpg = os.path.join(TEAM, f"{emp['slug']}.jpg")
    if os.path.exists(jpg):
        return circle(Image.open(jpg), pd)
    # No photo: initials on the card's placeholder grey (matches .ecard__photo--ph).
    disc = Image.new("RGBA", (pd, pd), (0, 0, 0, 0))
    dd = ImageDraw.Draw(disc)
    dd.ellipse([0, 0, pd - 1, pd - 1], fill=PLACEHOLDER_BG + (255,))
    font = load_font(800, int(pd * 0.30))
    txt = initials(emp["name"])
    bb = dd.textbbox((0, 0), txt, font=font)
    dd.text(((pd - (bb[2] - bb[0])) / 2 - bb[0], (pd - (bb[3] - bb[1])) / 2 - bb[1]),
            txt, font=font, fill=NAVY)
    return disc


def fit_font(draw, text, weight, start, min_size, max_w):
    size = start
    while size > min_size and draw.textlength(text, font=load_font(weight, size)) > max_w:
        size -= 2
    return load_font(weight, size)


def centered(draw, text, font, cx, y, fill):
    w = draw.textlength(text, font=font)
    draw.text((cx - w / 2, y), text, font=font, fill=fill)
    return draw.textbbox((0, 0), text, font=font)[3]


def render(emp: dict, out: str) -> None:
    # --- Background: the arch watermark, cover-fit like the card (center 42%) ---
    bg = cover(Image.open(os.path.join(E, "banner-bg.png")), W, H, oy=0.42)
    img = bg.convert("RGBA")
    draw = ImageDraw.Draw(img)
    cx = W // 2

    # --- Colour logo, centered near the top ---
    logo = Image.open(os.path.join(E, "logo.png")).convert("RGBA")
    lh = 78
    lw = round(logo.width * lh / logo.height)
    logo = logo.resize((lw, lh), Image.LANCZOS)
    img.alpha_composite(logo, (cx - lw // 2, 78))

    # --- Avatar: photo (94%) inside the green ring frame ---
    ax, ay = cx - D // 2, 245
    pd = round(D * PHOTO_RATIO)
    off = (D - pd) // 2
    img.alpha_composite(photo_disc(emp, pd), (ax + off, ay + off))
    ring = Image.open(os.path.join(E, "avatar-frame.png")).convert("RGBA").resize((D, D), Image.LANCZOS)
    img.alpha_composite(ring, (ax, ay))

    # --- Name (navy) + position (green), centered below the avatar ---
    max_w = W - 120
    y = ay + D + 70
    name_font = fit_font(draw, emp["name"], 700, 58, 38, max_w)
    y += centered(draw, emp["name"], name_font, cx, y, NAVY) + 18
    title_font = fit_font(draw, emp["title"], 700, 42, 26, max_w)
    centered(draw, emp["title"], title_font, cx, y, GREEN)

    img.convert("RGB").save(out, quality=92)


def main() -> None:
    with open(EMP, encoding="utf-8") as f:
        employees = json.load(f)
    os.makedirs(OUT_DIR, exist_ok=True)
    for e in employees:
        render(e, os.path.join(OUT_DIR, f"{e['slug']}.png"))
        print(f"{e['slug']:24s} -> public/e/og/{e['slug']}.png")
    print(f"\nWrote {len(employees)} OG images to {OUT_DIR}")


if __name__ == "__main__":
    main()
