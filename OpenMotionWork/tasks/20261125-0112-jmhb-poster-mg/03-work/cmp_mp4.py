# -*- coding: utf-8 -*-
"""Compare the exported MP4 last frame against the PDF reference and the local snapshot."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
from PIL import Image

BASE = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg"
ref = Image.open(os.path.join(BASE, "03-work", "page1_3x.png")).convert("RGB").resize((1080, 1920), Image.LANCZOS)
mp4 = Image.open(os.path.join(BASE, "04-deliver", "frames", "f07.png")).convert("RGB")
snap = Image.open(os.path.join(BASE, "03-work", "build-test", "shots4", "frame-00-at-5.9s.png")).convert("RGB")

for name, im in (("mp4", mp4), ("snapshot", snap)):
    a = np.asarray(im).astype(np.int16)
    r = np.asarray(ref).astype(np.int16)
    print(f"{name}: size={im.size} meanDiff={np.abs(a-r).mean():.2f}")
    # row profile: where does ink live?
    col = (a.mean(axis=2) < 200).sum(axis=1)
    rows = np.where(col > 3)[0]
    print("   ink rows:", rows.min() if len(rows) else None, rows.max() if len(rows) else None)
    colr = (r.mean(axis=2) < 200).sum(axis=1)
    rr = np.where(colr > 3)[0]
    print("   ref ink rows:", rr.min(), rr.max())

d = np.abs(np.asarray(mp4).astype(np.int16) - np.asarray(snap).astype(np.int16)).mean(axis=2)
print("mp4 vs snapshot mean diff:", round(float(d.mean()), 2))
Image.fromarray(((d / max(1, d.max())) * 255).astype(np.uint8)).save(os.path.join(BASE, "04-deliver", "diff-mp4-snap.png"))

sheet = Image.new("RGB", (1080 * 3 + 24, 1920), (20, 20, 20))
sheet.paste(ref, (0, 0)); sheet.paste(snap, (1080 + 12, 0)); sheet.paste(mp4, (2160 + 24, 0))
sheet.resize((sheet.width // 3, sheet.height // 3), Image.LANCZOS).save(os.path.join(BASE, "04-deliver", "side3.jpg"), quality=90)
print("saved side3.jpg")
