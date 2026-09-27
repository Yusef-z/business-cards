"""Shared loader for the tenant-aware scripts: `python3 scripts/x.py [tenant-id]`."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(argv=sys.argv) -> dict:
    tid = argv[1] if len(argv) > 1 else "watania"
    tdir = os.path.join(ROOT, "tenants", tid)
    with open(os.path.join(tdir, "tenant.json"), encoding="utf-8") as f:
        t = json.load(f)
    t["dir"] = tdir
    # Absent until build-employees.mjs has run (crop_photos.py runs before it).
    emp = os.path.join(tdir, "employees.json")
    t["employees"] = json.load(open(emp, encoding="utf-8")) if os.path.exists(emp) else []
    return t
