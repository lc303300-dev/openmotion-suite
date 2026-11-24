# -*- coding: utf-8 -*-
"""Extract embedded images and fonts from the source PDF."""
import json, sys, os, io
sys.stdout.reconfigure(encoding="utf-8")
import fitz

SRC = r"F:\LiuCan\Work\20261123-JMHB\画板 16(1).pdf"
BASE = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg"
IMG = os.path.join(BASE, "02-assets", "orig")
FNT = os.path.join(BASE, "02-assets", "fonts")
os.makedirs(IMG, exist_ok=True)
os.makedirs(FNT, exist_ok=True)

doc = fitz.open(SRC)
page = doc[0]
seen = {}
for im in page.get_images(full=True):
    xref = im[0]
    if xref in seen:
        continue
    info = doc.extract_image(xref)
    seen[xref] = True
    ext = info["ext"]
    name = f"xref{xref:03d}_{info['width']}x{info['height']}.{ext}"
    path = os.path.join(IMG, name)
    with open(path, "wb") as fh:
        fh.write(info["image"])
    print("IMG", name, len(info["image"]), "bytes", "cs=", im[5], "smask=", im[1])

for xref, ext, typ, base in [(f[1], f[2], f[3], f[4]) for f in doc.get_page_fonts(0)]:
    try:
        fname, fext, ftype, buf = doc.extract_font(xref)
        out = os.path.join(FNT, f"{fname}.{fext}")
        with open(out, "wb") as fh:
            fh.write(buf)
        print("FONT", fname, fext, ftype, len(buf), "->", out)
    except Exception as e:
        print("FONT FAIL", xref, base, e)

doc.close()
