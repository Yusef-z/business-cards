"""Generate a branded social-preview (Open Graph) image per employee.

Sharing an employee link on WhatsApp fed the tall portrait as og:image,
which the preview cropped/stretched. Instead we render a fixed vertical card
that mirrors the site's hero — the arch watermark, the colour logo, the photo
in the green ring frame, the navy name and green position — so the preview
always looks like the card itself.

Usage:  python3 scripts/make_og.py [tenant-id]   (default: watania)
Deps:   pillow, numpy, fonttools   (fonts: node_modules/@fontsource/changa)
Output: public/<tenant.assets>/og/<slug>.png  (820x900)
"""
import io
import json
import os

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

import tenant as tenant_mod

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TENANT = tenant_mod.load()
TEAM = os.path.join(ROOT, "public", TENANT["team"].lstrip("/"))
E = os.path.join(ROOT, "public", TENANT["assets"].lstrip("/"))
OUT_DIR = os.path.join(E, "og")
FONT_DIR = os.path.join(ROOT, "node_modules", "@fontsource", "changa", "files")

W, H = 820, 900
CARD_W = 430                  # the CSS card width the tenant's px values are written for


def hex_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


NAVY = hex_rgb(TENANT["colors"]["name"])            # .ecard__name
GREEN = hex_rgb(TENANT["colors"]["title"])          # .ecard__title
PLACEHOLDER_BG = hex_rgb(TENANT["colors"]["placeholder"])  # .ecard__photo--ph

# Avatar geometry mirrors the card: ring box D, photo at 94% inside it.
D = 360
PHOTO_RATIO = 0.94
HONORIFICS = {"dr", "mr", "mrs", "ms", "eng", "prof"}


def load_font(weight: int, size: int, script: str = "latin") -> ImageFont.FreeTypeFont:
    """Load Changa at a weight/size. The package ships .woff only, so
    convert to an in-memory TTF (FreeType/PIL can't read .woff directly)."""
    tt = TTFont(os.path.join(FONT_DIR, f"changa-{script}-{weight}-normal.woff"))
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


def centered(draw, text, font, cx, y, fill, rtl=False):
    # Arabic needs libraqm shaping (direction/language); Latin is left as-is.
    kw = {"direction": "rtl", "language": "ar"} if rtl else {}
    w = draw.textlength(text, font=font, **kw)
    draw.text((cx - w / 2, y), text, font=font, fill=fill, **kw)
    return draw.textbbox((0, 0), text, font=font, **kw)[3]


LOCKUP_GREY = (0x74, 0x74, 0x74)  # .ecard__lockup


def gradient_ring(d: int, width: int) -> Image.Image:
    """CSS .ecard__avatar--gradient: a diagonal brand-green ring, `width` px thick."""
    grad = Image.new("RGB", (d, d))
    px = grad.load()
    a, b = hex_rgb("#a8c243"), hex_rgb("#205c39")
    for y in range(d):
        for x in range(d):
            t = (x + y) / (2 * d - 2)
            px[x, y] = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
    mask = Image.new("L", (d, d), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([0, 0, d - 1, d - 1], fill=255)
    md.ellipse([width, width, d - 1 - width, d - 1 - width], fill=0)
    out = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    out.paste(grad, (0, 0), mask)
    return out


def render(emp: dict, out: str) -> None:
    # --- Background: the tenant banner, cover-fit like the card ---
    bg = cover(Image.open(os.path.join(E, "banner-bg.png")), W, H, oy=0.42)
    img = bg.convert("RGBA")
    draw = ImageDraw.Draw(img)
    cx = W // 2

    # --- Colour logo, centered near the top (+ lockup text lines when the
    #     logo image doesn't carry the company name itself) ---
    lockup = TENANT.get("lockup") or []
    tight = bool(lockup)  # the extra lines need the vertical rhythm compressed to fit 900px
    logo = Image.open(os.path.join(E, "logo.png")).convert("RGBA")
    lh = round(TENANT["logoHeight"] * W / CARD_W)
    lw = round(logo.width * lh / logo.height)
    logo = logo.resize((lw, lh), Image.LANCZOS)
    y = 50 if tight else 78
    img.alpha_composite(logo, (cx - lw // 2, y))
    y += lh
    if lockup:
        y += 14
        ar, en = lockup[0], lockup[1] if len(lockup) > 1 else ""
        y += centered(draw, ar, load_font(600, 30, "arabic"), cx, y, LOCKUP_GREY, rtl=True) + 4
        if en:
            y += centered(draw, en, load_font(600, 23), cx, y, LOCKUP_GREY)
        y += 26
    else:
        y += 89

    # --- Avatar: photo inside the ring (frame PNG, or a CSS-style gradient ring) ---
    ax, ay = cx - D // 2, y
    if TENANT.get("ring"):
        pd = round(D * PHOTO_RATIO)
        ring = Image.open(os.path.join(ROOT, "public", TENANT["ring"].lstrip("/"))).convert("RGBA").resize((D, D), Image.LANCZOS)
    else:
        pd = D - 2 * 8
        ring = gradient_ring(D, 8)
    off = (D - pd) // 2
    img.alpha_composite(photo_disc(emp, pd), (ax + off, ay + off))
    img.alpha_composite(ring, (ax, ay))

    # --- Name (navy) + position (green), centered below the avatar ---
    max_w = W - 120
    y = ay + D + (50 if tight else 70)
    name_font = fit_font(draw, emp["name"], 700, 58, 38, max_w)
    y += centered(draw, emp["name"], name_font, cx, y, NAVY) + (14 if tight else 18)
    title_font = fit_font(draw, emp["title"], 700, 42, 26, max_w)
    centered(draw, emp["title"], title_font, cx, y, GREEN)

    img.convert("RGB").save(out, quality=92)


def main() -> None:
    employees = TENANT["employees"]
    os.makedirs(OUT_DIR, exist_ok=True)
    for e in employees:
        render(e, os.path.join(OUT_DIR, f"{e['slug']}.png"))
        print(f"{e['slug']:24s} -> public{TENANT['assets']}/og/{e['slug']}.png")
    print(f"\nWrote {len(employees)} OG images to {OUT_DIR}")


if __name__ == "__main__":
    main()
