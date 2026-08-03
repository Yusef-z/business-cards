"""Generate a branded QR code per employee.

Rounded modules, black on white, high error correction, with the Al Watania
globe/W logo centered on a white pad (matches the approved sample). Each QR
encodes the employee's live card URL and is verified to still decode.

Usage:  python3 scripts/make_qr.py
Env:    SITE_URL   (default https://areez-qr.com)
        BASE_PATH  (default "", the site serves employee cards at the root)
Output: qrcodes/e/<slug>.png
"""
import json
import os

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.environ.get("SITE_URL", "https://areez-qr.com").rstrip("/")
BASE = os.environ.get("BASE_PATH", "").rstrip("/")
LOGO = os.path.join(ROOT, "scripts", "qrcode_logo.png")
OUT_DIR = os.path.join(ROOT, "qrcodes", "e")

# Logo geometry as a fraction of the QR width.
PAD_RATIO = 0.30   # white clear-zone behind the logo
LOGO_RATIO = 0.225


def make_qr(url: str, out_path: str) -> None:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=24, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        color_mask=SolidFillColorMask(front_color=(0, 0, 0), back_color=(255, 255, 255)),
    ).convert("RGBA")
    w, h = img.size

    pad = int(w * PAD_RATIO)
    draw = ImageDraw.Draw(img)
    x0, y0 = (w - pad) // 2, (h - pad) // 2
    draw.rounded_rectangle([x0, y0, x0 + pad, y0 + pad], radius=int(pad * 0.16), fill=(255, 255, 255, 255))

    logo = Image.open(LOGO).convert("RGBA")
    lw = int(w * LOGO_RATIO)
    logo.thumbnail((lw, lw), Image.LANCZOS)
    img.alpha_composite(logo, ((w - logo.width) // 2, (h - logo.height) // 2))
    img.convert("RGB").save(out_path)


def verify(url: str, path: str):
    """Decode the generated QR to confirm the logo didn't break it.
    Returns True/False, or None if no decoder (OpenCV) is installed."""
    try:
        import cv2
    except ImportError:
        return None
    data, _, _ = cv2.QRCodeDetector().detectAndDecode(cv2.imread(path))
    return data == url


def main() -> None:
    with open(os.path.join(ROOT, "src", "data", "employees.json"), encoding="utf-8") as f:
        employees = json.load(f)
    os.makedirs(OUT_DIR, exist_ok=True)

    failures = []
    for e in employees:
        url = f"{SITE}{BASE}/e/{e['slug']}"
        out = os.path.join(OUT_DIR, f"{e['slug']}.png")
        make_qr(url, out)
        ok = verify(url, out)
        tag = {True: "OK ", False: "BAD", None: "-- "}[ok]
        print(f"{tag}  {e['slug']:24s} -> {url}")
        if ok is False:
            failures.append(e["slug"])

    print(f"\nWrote {len(employees)} QR codes to {OUT_DIR}")
    if failures:
        raise SystemExit(f"ERROR: {len(failures)} QR code(s) failed to decode: {failures}")


if __name__ == "__main__":
    main()
