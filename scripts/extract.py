#!/usr/bin/env python3
"""Extract association data from the source Excel into src/data/associations.json.
Pure stdlib (zipfile + ElementTree) — no third-party deps. Re-runnable."""
import zipfile, re, json, sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
XLSX = ROOT / "دليل الجمعيات.xlsx"
OUT = ROOT / "src" / "data" / "associations.json"
M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

# Row (in sheet «قاعدة بيانات الجمعيات», sheet3) -> immutable slug. Rows 3..24.
ROW_SLUG = {
    3: "wim", 4: "mining", 5: "datem", 6: "pmg", 7: "amasca", 8: "iia",
    9: "exporters", 10: "saudiscp", 11: "slamatc", 12: "pia",
    13: "industrialfuture", 14: "mdma", 15: "sidam", 16: "chemical",
    17: "tahfez", 18: "food", 19: "aircraft", 20: "jba", 21: "bma",
    22: "fma", 23: "mema", 24: "ela",
}

# Cells that hold descriptive text / wrong or corrupted values.
# Verified against each association's email + website domain during design.
OVERRIDES = {
    "chemical": {"x": "https://x.com/chemicalsa_sa"},   # cell: "(1) … (@chemicalsa_sa) / X"
    "fma": {"linkedin": None},                           # cell: a page-title string, no URL
    "mema": {"linkedin": None, "website": "https://www.mema.org.sa"},  # LI was a /posts/ link
    "mdma": {"website": "https://www.mdma.org.sa"},      # cell held Arabic text
}

def load(sheet_path):
    z = zipfile.ZipFile(XLSX)
    ss = ET.fromstring(z.read("xl/sharedStrings.xml"))
    strings = ["".join(t.text or "" for t in si.iter(M + "t")) for si in ss]
    sh = ET.fromstring(z.read(sheet_path))
    cells = {}
    for c in sh.iter(M + "c"):
        ref = c.get("r")
        if not ref:
            continue
        col = re.match(r"[A-Z]+", ref).group()
        row = int(re.search(r"\d+", ref).group())
        v = c.find(M + "v")
        val = v.text if v is not None else ""
        if c.get("t") == "s" and val != "":
            val = strings[int(val)]
        cells.setdefault(row, {})[col] = val
    return cells

def is_url(s):
    return bool(s) and s.strip() not in ("--", "") and re.match(r"https?://|www\.", s.strip())

def norm_url(s):
    s = s.strip()
    return s if s.startswith("http") else "https://" + s

def clean_email(e):
    e = (e or "").strip().lower().replace("_x0001_", "-")
    return e or None

def clean_phone(p):
    d = re.sub(r"\D", "", p or "")
    if not d:
        return None
    if d.startswith("0"):
        d = d[1:]
    return "+966" + d

def build():
    cells = load("xl/worksheets/sheet3.xml")
    out = []
    for row in range(3, 25):
        r = cells.get(row, {})
        slug = ROW_SLUG[row]
        ov = OVERRIDES.get(slug, {})
        rec = {"slug": slug, "name": r.get("A", "").strip()}
        ph = clean_phone(r.get("H", ""))
        if ph:
            rec["phone"] = ph
        em = ov["email"] if "email" in ov else clean_email(r.get("G", ""))
        if em:
            rec["email"] = em
        web = ov["website"] if "website" in ov else (norm_url(r["F"]) if is_url(r.get("F", "")) else None)
        if web:
            rec["website"] = web
        li = ov["linkedin"] if "linkedin" in ov else (r["B"].strip() if is_url(r.get("B", "")) else None)
        if li:
            rec["linkedin"] = li
        x = ov["x"] if "x" in ov else (r["D"].strip() if is_url(r.get("D", "")) else None)
        if x:
            rec["x"] = x
        rec["logo"] = f"/logos/{slug}.png"
        out.append(rec)
    return out

def main():
    data = build()
    assert len(data) == 22, f"expected 22 records, got {len(data)}"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(data)} records to {OUT}")

if __name__ == "__main__":
    sys.exit(main())
