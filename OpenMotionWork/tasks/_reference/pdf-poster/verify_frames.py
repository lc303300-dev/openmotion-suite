# -*- coding: utf-8 -*-
"""verify_frames.py — 把渲染帧和参考图做逐像素比对，输出可判断的数字。

不要靠肉眼看缩略图判断"像不像"（很容易把对的看歪）。这个脚本给三个硬指标：
  1. meanDiff   平均像素差（0–255）。同一版面正常在 3–8 之间；
                文字抗锯齿、阴影近似会带来 3–5 的底噪。
  2. ink rows   "有内容"的行范围。和参考差 1–2 行说明对位没问题；
                差几十行就是整体偏移或漏渲染。
  3. diff.png   差异热图，白 = 差得多，一眼看出是哪种错位。

用法:
    python verify_frames.py <ref.png> <candidate.png|dir> [--out dir]

    ref       参考图（PDF 用 fitz 渲到同尺寸，或用 page1_3x.png 缩放）
    candidate 单帧，或目录（取前 N 张逐一比）
"""
from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np
from PIL import Image


def ink_rows(rgb, threshold=200, min_px=3):
    col = (rgb.mean(axis=2) < threshold).sum(axis=1)
    rows = np.where(col >= min_px)[0]
    return (int(rows.min()), int(rows.max())) if len(rows) else (None, None)


def ink_cols(rgb, threshold=200, min_px=3):
    row = (rgb.mean(axis=2) < threshold).sum(axis=0)
    cols = np.where(row >= min_px)[0]
    return (int(cols.min()), int(cols.max())) if len(cols) else (None, None)


def compare(ref_path, cand_path, outdir):
    ref = Image.open(ref_path).convert("RGB")
    cand = Image.open(cand_path).convert("RGB")
    if ref.size != cand.size:
        cand = cand.resize(ref.size, Image.LANCZOS)
    R = np.asarray(ref).astype(np.int16)
    C = np.asarray(cand).astype(np.int16)
    d = np.abs(R - C).mean(axis=2)
    rr, rc = ink_rows(R), ink_cols(R)
    cr, cc = ink_rows(C), ink_cols(C)
    row = {
        "candidate": os.path.basename(cand_path),
        "size": list(ref.size),
        "mean_diff": round(float(d.mean()), 2),
        "p99_diff": round(float(np.percentile(d, 99)), 1),
        "ref_ink_rows": rr, "cand_ink_rows": cr,
        "ref_ink_cols": rc, "cand_ink_cols": cc,
        "row_shift": (cr[0] - rr[0], cr[1] - rr[1]) if rr[0] is not None and cr[0] is not None else None,
        "col_shift": (cc[0] - rc[0], cc[1] - rc[1]) if rc[0] is not None and cc[0] is not None else None,
    }
    if outdir:
        os.makedirs(outdir, exist_ok=True)
        stem = os.path.splitext(os.path.basename(cand_path))[0]
        Image.fromarray(((d / max(1.0, d.max())) * 255).astype(np.uint8)).save(
            os.path.join(outdir, f"diff-{stem}.png"))
    return row


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    ref_path, cand = argv[1], argv[2]
    outdir = argv[4] if len(argv) > 4 and argv[3] == "--out" else None

    if os.path.isdir(cand):
        files = sorted(glob.glob(os.path.join(cand, "*.png")))[:12]
    else:
        files = [cand]

    rows = [compare(ref_path, f, outdir) for f in files]
    for r in rows:
        print(f"{r['candidate']:28s} meanDiff={r['mean_diff']:6.2f}  p99={r['p99_diff']:6.1f}  "
              f"rows {r['ref_ink_rows']} → {r['cand_ink_rows']} (shift {r['row_shift']})")
    if len(rows) > 1:
        avg = sum(r["mean_diff"] for r in rows) / len(rows)
        print(f"\n平均 meanDiff = {avg:.2f}")
    if outdir:
        with open(os.path.join(outdir, "verify.json"), "w", encoding="utf-8") as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main(sys.argv))
