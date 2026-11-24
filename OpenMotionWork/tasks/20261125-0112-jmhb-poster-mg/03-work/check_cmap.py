# -*- coding: utf-8 -*-
"""Check cmap coverage of extracted fonts."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
from fontTools.ttLib import TTFont

FNT = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg\02-assets\fonts"
need_cn = "武汉小学武珞路中学双本部名校为邻让成长拥有更确定的归处"
need_en = "POLY RARE CENTRO"
need_small = ("WUHAN PRIMARY SCHOOL / WULUOLU MIDDLE SCHOOL "
              "ADJACENT TO THE DUAL HOME-CAMPUS PRESTIGIOUS SCHOOLS, "
              "GIVING GROWTH A MORE CERTAIN PLACE TO BELONG.")

for fn in sorted(os.listdir(FNT)):
    if not fn.endswith((".ttf", ".otf")):
        continue
    p = os.path.join(FNT, fn)
    f = TTFont(p, lazy=True)
    cmap = f.getBestCmap() or {}
    fam = f["name"].getDebugName(1) if "name" in f else "?"
    print("=" * 70)
    print(fn, "| family:", fam, "| glyphs:", len(f.getGlyphOrder()), "| cmap entries:", len(cmap))
    for label, need in (("CN", need_cn), ("LOGO", need_en), ("small", need_small)):
        missing = sorted({c for c in need if ord(c) not in cmap and c != " "})
        if need in (need_cn, need_en):
            print(f"  {label}: missing={''.join(missing) or 'NONE'}")
        else:
            print(f"  {label}: missing={''.join(missing) or 'NONE'}")
    if cmap:
        sample = "".join(chr(c) for c in sorted(cmap))
        print("  first chars:", sample[:120])
    f.close()
