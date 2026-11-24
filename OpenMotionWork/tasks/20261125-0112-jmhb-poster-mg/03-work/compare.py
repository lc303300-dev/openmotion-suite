# -*- coding: utf-8 -*-
"""Compare PDF render vs project render, region by region."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
from PIL import Image

BASE = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg"
ref = Image.open(os.path.join(BASE, "03-work", "page1_3x.png")).convert("RGB").resize((1080, 1920), Image.LANCZOS)
cur = Image.open(os.path.join(BASE, "03-work", "build-test", "shots4", "frame-00-at-5.9s.png")).convert("RGB")

R = np.asarray(ref).astype(np.int16)
C = np.asarray(cur).astype(np.int16)
d = np.abs(R - C).mean(axis=2)
print("overall mean diff:", round(float(d.mean()), 2))

regions = {
    "bg_top_strip":      (0, 0, 1080, 200),
    "logo":              (200, 200, 900, 400),
    "photos":            (0, 380, 1080, 1260),
    "school_line":       (200, 1270, 900, 1360),
    "copy_lines":        (150, 1360, 950, 1520),
    "english":           (150, 1520, 950, 1640),
    "bottom_bg":         (0, 1700, 1080, 1920),
}
for name, (x0, y0, x1, y1) in regions.items():
    sub_r = R[y0:y1, x0:x1]
    sub_c = C[y0:y1, x0:x1]
    print(f"{name:14s} ref_mean={sub_r.reshape(-1,3).mean(axis=0).round(1)} "
          f"cur_mean={sub_c.reshape(-1,3).mean(axis=0).round(1)} "
          f"diff={np.abs(sub_r - sub_c).mean():.2f}")

# save side-by-side + diff map
out = os.path.join(BASE, "03-work", "compare")
os.makedirs(out, exist_ok=True)
Image.fromarray(((d / max(1, d.max())) * 255).astype(np.uint8)).save(os.path.join(out, "diff.png"))
w, h = 1080, 1920
sheet = Image.new("RGB", (w * 2 + 24, h), (20, 20, 20))
sheet.paste(ref, (0, 0))
sheet.paste(cur, (w + 24, 0))
sheet.resize((sheet.width // 2, sheet.height // 2), Image.LANCZOS).save(os.path.join(out, "side.jpg"), quality=88)
print("saved compare/diff.png and side.jpg")

# sample specific pixels
for pt in [(40, 100), (540, 60), (1000, 1800), (540, 1300)]:
    x, y = pt
    print(f"px {pt}: ref={tuple(R[y,x])} cur={tuple(C[y,x])}")
