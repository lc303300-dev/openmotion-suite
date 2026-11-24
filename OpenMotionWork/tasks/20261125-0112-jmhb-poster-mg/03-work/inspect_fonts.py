# -*- coding: utf-8 -*-
"""Inspect extracted fonts (cmap coverage) and image placement rects."""
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8")
import fitz

BASE = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg"
SRC = r"F:\LiuCan\Work\20261123-JMHB\画板 16(1).pdf"

# ---- image placement
doc = fitz.open(SRC)
page = doc[0]
for xref in [67, 69, 70, 72, 73, 74, 76, 54]:
    rects = page.get_image_rects(xref, transform=False)
    print("xref", xref, "rects:", [[round(v, 2) for v in r] for r in rects])
    try:
        infos = page.get_image_info(xrefs=[xref])
        for info in infos:
            print("   info bbox", [round(v, 2) for v in info["bbox"]],
                  "transform", [round(v, 4) for v in info["transform"]],
                  "w/h", info["width"], info["height"])
    except Exception as e:
        print("   info fail", e)
doc.close()

# ---- fonts
print("\n=== FONTS ===")
FNT = os.path.join(BASE, "02-assets", "fonts")
try:
    from fontTools.ttLib import TTFont
    for fn in os.listdir(FNT):
        p = os.path.join(FNT, fn)
        if fn.endswith((".ttf", ".otf")):
            try:
                f = TTFont(p, fontNumber=0, lazy=True)
                cmap = f.getBestCmap() if f.get("cmap") else {}
                name = f["name"].getDebugName(1) if "name" in f else "?"
                print(fn, "| family:", name, "| glyphs:", len(f.getGlyphOrder()),
                      "| cmap:", len(cmap))
                chars = "".join(chr(c) for c in sorted(cmap)[:400])
                print("   chars:", chars[:400])
            except Exception as e:
                print(fn, "OPEN FAIL", e)
except ImportError:
    print("no fontTools")
