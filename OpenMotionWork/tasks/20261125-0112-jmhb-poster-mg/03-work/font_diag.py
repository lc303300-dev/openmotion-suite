# -*- coding: utf-8 -*-
"""Inspect subset font tables and rebuild a importable TTF (post/name/os2 filled)."""
import sys, os, re
sys.stdout.reconfigure(encoding="utf-8")
import fitz
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable

BASE = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg"
FNT = os.path.join(BASE, "02-assets", "fonts")
OUT = os.path.join(BASE, "02-assets", "fonts-web")
os.makedirs(OUT, exist_ok=True)

for fn in ["QGGUPM+HarmonyOS_Sans_SC_Medium.ttf", "IXDTHC+HarmonyOS_Sans_SC_Light.ttf"]:
    p = os.path.join(FNT, fn)
    tt = TTFont(p, lazy=False)
    print("=" * 60)
    print(fn, "tables:", sorted(tt.keys()))
    print("  head.unitsPerEm:", tt["head"].unitsPerEm, "flags:", hex(tt["head"].flags))
    print("  hhea:", tt["hhea"].ascent, tt["hhea"].descent, "numberOfHMetrics:", tt["hhea"].numberOfHMetrics)
    print("  maxp.numGlyphs:", tt["maxp"].numGlyphs)
    if "post" in tt:
        print("  post.formatType:", tt["post"].formatType, "italicAngle:", getattr(tt["post"], "italicAngle", "MISSING"))
    if "name" in tt:
        print("  name ids:", sorted({r.nameID for r in tt["name"].names}))
        for nid in (1, 2, 4, 6):
            try:
                print("   ", nid, tt["name"].getDebugName(nid))
            except Exception as e:
                print("   ", nid, "n/a")
    if "OS/2" in tt:
        print("  OS/2 weight:", tt["OS/2"].usWeightClass, "fsSelection:", hex(tt["OS/2"].fsSelection))
    tt.close()
