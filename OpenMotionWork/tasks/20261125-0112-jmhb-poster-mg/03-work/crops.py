# -*- coding: utf-8 -*-
"""Crop matching regions from reference and current render for close comparison."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
from PIL import Image

BASE = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg"
ref = Image.open(os.path.join(BASE, "03-work", "page1_3x.png")).convert("RGB").resize((1080, 1920), Image.LANCZOS)
cur = Image.open(os.path.join(BASE, "03-work", "build-test", "shots3", "frame-00-at-5.9s.png")).convert("RGB")
out = os.path.join(BASE, "03-work", "compare")
os.makedirs(out, exist_ok=True)

crops = {
    "logo":    (250, 220, 830, 400),
    "stamp":   (80, 950, 400, 1230),
    "note":    (600, 420, 940, 720),
    "english": (200, 1520, 900, 1650),
    "school":  (220, 1270, 860, 1380),
}
for name, box in crops.items():
    r = ref.crop(box)
    c = cur.crop(box)
    w, h = r.size
    sheet = Image.new("RGB", (w * 2 + 12, h), (30, 30, 30))
    sheet.paste(r, (0, 0))
    sheet.paste(c, (w + 12, 0))
    scale = 2 if w < 420 else 1.6
    sheet = sheet.resize((int(sheet.width * scale), int(sheet.height * scale)), Image.LANCZOS)
    p = os.path.join(out, f"cmp-{name}.png")
    sheet.save(p)
    print(name, sheet.size, p)
