# -*- coding: utf-8 -*-
"""Color diagnostics: why the stamp looks brighter than the PDF render."""
import sys, os, io
sys.stdout.reconfigure(encoding="utf-8")
import fitz
import numpy as np
from PIL import Image

BASE = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg"
SRC = r"F:\LiuCan\Work\20261123-JMHB\画板 16(1).pdf"
doc = fitz.open(SRC)
page = doc[0]

# 1. raw extracted png (what I used)
png = Image.open(os.path.join(BASE, "02-assets", "web", "stamp.png")).convert("RGBA")
a = np.array(png)
op = a[a[..., 3] > 200][:, :3]
print("stamp.png opaque mean:", op.mean(axis=0).round(1), "n=", len(op))

# 2. PDF render of the stamp area (colour managed)
clip = fitz.Rect(71.75, 683.14, 311.47, 798.61)
pix = page.get_pixmap(matrix=fitz.Matrix(6, 6), clip=clip, alpha=False)
pix.save(os.path.join(BASE, "03-work", "stamp_ref_6x.png"))
r = np.array(Image.open(os.path.join(BASE, "03-work", "stamp_ref_6x.png")).convert("RGB")).astype(np.int16)
print("render area mean:", r.reshape(-1, 3).mean(axis=0).round(1))

# dark pixels in render = stamp ink
mask = (r.sum(axis=2) < 500)
print("render ink px:", int(mask.sum()), "mean:", r[mask].mean(axis=0).round(1) if mask.sum() else "-")

# 3. fitz Pixmap with colour conversion
im = doc.extract_image(76)
print("extract info:", {k: v for k, v in im.items() if k != "image"})
p = fitz.Pixmap(doc, 76)
print("pixmap cs:", p.colorspace.name if p.colorspace else None, "n:", p.n, "alpha:", p.alpha)
try:
    p2 = fitz.Pixmap(fitz.csRGB, p)
    p2.save(os.path.join(BASE, "03-work", "stamp_fitz_rgb.png"))
    arr = np.frombuffer(p2.samples, dtype=np.uint8).reshape(p2.h, p2.w, p2.n)
    print("fitz rgb mean:", arr.reshape(-1, p2.n).mean(axis=0).round(1))
except Exception as ex:
    print("convert fail:", ex)

# 4. compare my stamp ink colour vs render ink colour
ink = a[(a[..., 3] > 200)]
print("stamp.png ink mean (alpha>200):", ink[:, :3].mean(axis=0).round(1))

# 5. photo colour check
for name, rect in [("middle", (65.21, 505.11, 598.44, 802.87)),
                   ("paper", (0, 0, 720, 200))]:
    px = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=fitz.Rect(*rect))
    arr = np.frombuffer(px.samples, dtype=np.uint8).reshape(px.h, px.w, px.n)[..., :3]
    print(f"{name} pdf-render mean:", arr.reshape(-1, 3).mean(axis=0).round(1))

for name, f in [("middle.jpg", "02-assets/project/middle.jpg"), ("paper.jpg", "02-assets/project/paper.jpg")]:
    im = Image.open(os.path.join(BASE, f)).convert("RGB")
    arr = np.array(im)
    print(f"{name} asset mean:", arr.reshape(-1, 3).mean(axis=0).round(1))
doc.close()
