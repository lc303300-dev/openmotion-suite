# -*- coding: utf-8 -*-
"""Measure frame PNG border widths and stamp alpha; report exact colors."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
from PIL import Image

IMG = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg\02-assets\orig"

for name in ["xref072_497x683.png", "xref076_333x161.png", "xref069_242x324.jpeg"]:
    p = os.path.join(IMG, name)
    im = Image.open(p)
    print("=" * 60)
    print(name, im.mode, im.size, "info:", {k: v for k, v in im.info.items() if k in ("transparency", "icc_profile")})
    a = np.array(im.convert("RGBA"))
    print("  alpha min/max:", a[..., 3].min(), a[..., 3].max(), "| opaque px:", int((a[..., 3] > 250).sum()))

# frame: find white band + inner transparent window
im = Image.open(os.path.join(IMG, "xref072_497x683.png")).convert("RGBA")
a = np.array(im)
h, w = a.shape[:2]
alpha = a[..., 3]
white = (a[..., 0] > 240) & (a[..., 1] > 240) & (a[..., 2] > 240) & (alpha > 200)
row = white[h // 2]
col = white[:, w // 2]
print("\nframe mid-row white cols:", np.where(row)[0][:8], "...", np.where(row)[0][-8:])
print("frame mid-col white rows:", np.where(col)[0][:8], "...", np.where(col)[0][-8:])
print("left band px:", int(np.where(~white[h // 2])[0][0]) if (~white[h//2]).any() else "?")
# scan from left for the first non-white (inner) pixel
xs = np.where(~row)[0]
ys = np.where(~col)[0]
print("inner window x:", xs.min() if len(xs) else None, xs.max() if len(xs) else None)
print("inner window y:", ys.min() if len(ys) else None, ys.max() if len(ys) else None)
print("frame W,H:", w, h)
if len(xs) and len(ys):
    print("border px: left", xs.min(), "right", w - 1 - xs.max(), "top", ys.min(), "bottom", h - 1 - ys.max())
    print("border pct: left %.2f%% right %.2f%% top %.2f%% bottom %.2f%%" % (
        100 * xs.min() / w, 100 * (w - 1 - xs.max()) / w,
        100 * ys.min() / h, 100 * (h - 1 - ys.max()) / h))

# stamp colors
im2 = np.array(Image.open(os.path.join(IMG, "xref076_333x161.png")).convert("RGBA"))
op = im2[im2[..., 3] > 200][:, :3]
print("\nstamp opaque colors: n=", len(op), "median=", np.median(op, axis=0), "mean=", op.mean(axis=0).round(1))

# stamp bbox in image
alpha2 = im2[..., 3]
ys2, xs2 = np.where(alpha2 > 40)
print("stamp content bbox:", xs2.min(), xs2.max(), ys2.min(), ys2.max(), "of", im2.shape[1], im2.shape[0])

# background paper color
bg = np.array(Image.open(os.path.join(IMG, "xref067_1300x2815.jpeg")).convert("RGB"))
print("\npaper mean:", bg.reshape(-1, 3).mean(axis=0).round(1), "| median:", np.median(bg.reshape(-1, 3), axis=0))
