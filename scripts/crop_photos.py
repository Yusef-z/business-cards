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
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "photos")
OUT = os.path.join(ROOT, "public", "team")
MODEL = os.path.join(ROOT, "scripts", "models", "face_yunet.onnx")

SIZE = 600        # output avatar size (px, square)
CROP_MULT = 2.0   # crop side = 2.0x the detected face height (head + shoulders)
FACE_V = 0.44     # place the face centre at 44% of the crop height


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
        x, y = (w - s) // 2, (h - s) // 2
        note = "centre crop (no face found)"
    else:
        fcx, fcy, fh = fc
        s = min(int(fh * CROP_MULT), w, h)
        x = max(0, min(int(fcx - s / 2), w - s))
        y = max(0, min(int(fcy - s * FACE_V), h - s))
        note = "face-centred"
    im.crop((x, y, x + s, y + s)).resize((SIZE, SIZE), Image.LANCZOS).save(
        out, quality=88, optimize=True
    )
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
