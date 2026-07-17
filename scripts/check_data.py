#!/usr/bin/env python3
"""Validate src/data/associations.json. Exit non-zero on the first violation."""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data" / "associations.json"
LOGO_DIR = ROOT / "public" / "logos"

SLUG_RE = re.compile(r"^[a-z0-9]+$")
PHONE_RE = re.compile(r"^\+9665\d{8}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

EXPECTED_SLUGS = {
    "wim", "mining", "datem", "pmg", "amasca", "iia", "exporters", "saudiscp",
    "slamatc", "pia", "industrialfuture", "mdma", "sidam", "chemical", "tahfez",
    "food", "aircraft", "jba", "bma", "fma", "mema", "ela",
}

def fail(msg):
    print(f"check_data: FAIL — {msg}", file=sys.stderr)
    sys.exit(1)

def main(check_logos=False):
    data = json.loads(DATA.read_text(encoding="utf-8"))
    if len(data) != 22:
        fail(f"expected 22 records, got {len(data)}")
    slugs = [r["slug"] for r in data]
    if len(set(slugs)) != 22:
        fail("duplicate slug(s)")
    if set(slugs) != EXPECTED_SLUGS:
        fail(f"slug set mismatch: {set(slugs) ^ EXPECTED_SLUGS}")
    for r in data:
        s = r["slug"]
        if not SLUG_RE.match(s):
            fail(f"{s}: bad slug format")
        if not r.get("name", "").strip():
            fail(f"{s}: empty name")
        if r.get("logo") != f"/logos/{s}.png":
            fail(f"{s}: logo path mismatch")
        if "phone" in r and not PHONE_RE.match(r["phone"]):
            fail(f"{s}: phone not E.164 (+9665XXXXXXXX): {r['phone']}")
        if "email" in r and not EMAIL_RE.match(r["email"]):
            fail(f"{s}: bad email: {r['email']}")
        for k in ("website", "linkedin", "x"):
            if k in r and not r[k].startswith("https://"):
                fail(f"{s}: {k} must start with https:// : {r[k]}")
        if check_logos and not (LOGO_DIR / f"{s}.png").exists():
            fail(f"{s}: missing logo file public/logos/{s}.png")
    print(f"check_data: OK — 22 records valid" + (" (logos present)" if check_logos else ""))

if __name__ == "__main__":
    main(check_logos="--logos" in sys.argv)
