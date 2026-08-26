"""Face-centered square crops for employee avatars.

Reads raw photos from photos/<slug>.<ext>, detects the largest face with
OpenCV's YuNet detector, and writes a 600x600 JPEG cropped square and centred
on the face (head + shoulders) to public/team/<slug>.jpg. Falls back to a
plain centre crop when no face is found. The generator (build-employees.mjs)
then auto-attaches these to the cards.

Usage: python3 scripts/crop_photos.py
Deps:  pip install "opencv-python" pillow   (model: scripts/models/face_yunet.onnx)
"""
import glob
import os

import cv2
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "photos")
OUT = os.path.join(ROOT, "public", "team")
MODEL = os.path.join(ROOT, "scripts", "models", "face_yunet.onnx")

SIZE = 600        # output avatar size (px, square)
CROP_MULT = 2.3   # crop side = 2.3x the detected face height (head + shoulders)
FACE_V = 0.47     # face centre sits at 47% of the crop height (extra room for hair)
FACE_H = 0.0      # face centre sits at (50% + FACE_H) horizontally (+ = right)


def face_center(path):
    img = cv2.imread(path)
    if img is None:
        return None
    h, w = img.shape[:2]
    det = cv2.FaceDetectorYN.create(MODEL, "", (w, h), score_threshold=0.6)
    _, faces = det.detect(img)
    if faces is None or len(faces) == 0:
        return None
    f = max(faces, key=lambda f: f[2] * f[3])
    fx, fy, fw, fh = (float(v) for v in f[:4])
    return fx + fw / 2, fy + fh / 2, fh


def crop_one(path, out):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    fc = face_center(path)
    if fc is None:
        s = min(w, h)
        x0, y0 = (w - s) // 2, (h - s) // 2
        crop = im.crop((x0, y0, x0 + s, y0 + s))
        note = "centre crop (no face found)"
    else:
        fcx, fcy, fh = fc
        s = int(fh * CROP_MULT)
        # Target face position in the crop: (50% + FACE_H) across, FACE_V down.
        x0 = int(fcx - s * (0.5 + FACE_H))
        y0 = int(fcy - s * FACE_V)
        x1, y1 = x0 + s, y0 + s
        # Extend the edges (replicate border pixels) rather than clamp, so the
        # face lands exactly where we want even near an edge — and the fill
        # matches the real background instead of a guessed colour (no grey bar).
        pl, pt, pr, pb = max(0, -x0), max(0, -y0), max(0, x1 - w), max(0, y1 - h)
        if pl or pt or pr or pb:
            arr = np.pad(np.asarray(im), ((pt, pb), (pl, pr), (0, 0)), mode="edge")
            im = Image.fromarray(arr)
            x0, y0, x1, y1 = x0 + pl, y0 + pt, x1 + pl, y1 + pt
        crop = im.crop((x0, y0, x1, y1))
        note = "face-centred"
    crop.resize((SIZE, SIZE), Image.LANCZOS).save(out, quality=88, optimize=True)
    return note


def main():
    os.makedirs(OUT, exist_ok=True)
    files = sorted(
        f for f in glob.glob(os.path.join(SRC, "*"))
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
    )
    if not files:
        print(f"No raw photos in {SRC}/  (drop files named <slug>.<ext>)")
        return
    for p in files:
        slug = os.path.splitext(os.path.basename(p))[0]
        note = crop_one(p, os.path.join(OUT, f"{slug}.jpg"))
        print(f"{slug:24s} -> public/team/{slug}.jpg  ({note})")


if __name__ == "__main__":
    main()
