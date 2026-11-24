# -*- coding: utf-8 -*-
"""Composite PDF soft masks into alpha channels and export clean PNG assets."""
import sys, os, io
sys.stdout.reconfigure(encoding="utf-8")
import fitz
import numpy as np
from PIL import Image

SRC = r"F:\LiuCan\Work\20261123-JMHB\画板 16(1).pdf"
BASE = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg"
OUT = os.path.join(BASE, "02-assets", "web")
os.makedirs(OUT, exist_ok=True)
doc = fitz.open(SRC)

def img_with_mask(xref):
    info = doc.extract_image(xref)
    base = Image.open(io.BytesIO(info["image"]))
    sm = info.get("smask", 0)
    if sm:
        sminfo = doc.extract_image(sm)
        mask = Image.open(io.BytesIO(sminfo["image"])).convert("L")
        print(f"  xref{xref}: {base.mode} {base.size}, smask xref{sm} -> {mask.mode} {mask.size}")
        base = base.convert("RGBA")
        if mask.size != base.size:
            mask = mask.resize(base.size, Image.LANCZOS)
        base.putalpha(mask)
    else:
        print(f"  xref{xref}: {base.mode} {base.size}, no smask")
    return base

assets = {
    "paper.jpg": 67,
    "frame.png": 72,
    "stamp.png": 76,
    "note.png": 69,
    "gate.jpg": 70,      # 牌坊 / 汉江书院
    "primary.jpg": 73,   # 武汉小学
    "middle.jpg": 74,    # 武珞路中学
}
for name, xref in assets.items():
    im = img_with_mask(xref)
    out = os.path.join(OUT, name)
    if name.endswith(".jpg"):
        im.convert("RGB").save(out, quality=95, subsampling=0)
    else:
        im.save(out)
    print(" ->", out, im.size)

# report bbox of alpha content for frame & stamp
for name in ("frame.png", "stamp.png"):
    im = Image.open(os.path.join(OUT, name)).convert("RGBA")
    a = np.array(im)[..., 3]
    ys, xs = np.where(a > 30)
    print(f"\n{name}: size={im.size} content bbox x {xs.min()}-{xs.max()} y {ys.min()}-{ys.max()}")
    if name == "frame.png":
        # scan the middle row for opaque runs
        mid = a[a.shape[0]//2]
        on = np.where(mid > 200)[0]
        print("  mid-row opaque spans:", on.min(), on.max())
        gaps = np.where(np.diff(on) > 1)[0]
        print("  gaps at:", [(int(on[g]), int(on[g+1])) for g in gaps][:6])
        midc = a[:, a.shape[1]//2]
        onc = np.where(midc > 200)[0]
        gapsc = np.where(np.diff(onc) > 1)[0]
        print("  mid-col opaque spans:", onc.min(), onc.max())
        print("  gaps at:", [(int(onc[g]), int(onc[g+1])) for g in gapsc][:6])
doc.close()
