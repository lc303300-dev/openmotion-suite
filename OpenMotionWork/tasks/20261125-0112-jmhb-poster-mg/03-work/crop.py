# -*- coding: utf-8 -*-
"""Crop regions from the 3x page render for close inspection."""
import os, sys
sys.stdout.reconfigure(encoding="utf-8")
from PIL import Image

BASE = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg\03-work"
src = Image.open(os.path.join(BASE, "page1_3x.png"))
S = 3.0
crops = {
    "logo":      (150, 130, 570, 285),
    "stamp":     (40, 630, 220, 820),
    "photos":    (0, 260, 720, 860),
    "texts":     (140, 830, 580, 1120),
    "photo_tl":  (40, 280, 400, 560),
}
for name, (x0, y0, x1, y1) in crops.items():
    box = tuple(int(v * S) for v in (x0, y0, x1, y1))
    im = src.crop(box)
    out = os.path.join(BASE, f"crop_{name}.png")
    im.save(out)
    print(name, im.size, out)
