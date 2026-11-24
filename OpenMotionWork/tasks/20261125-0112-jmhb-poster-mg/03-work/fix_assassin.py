# -*- coding: utf-8 -*-
"""Fix Assassin subset font: add post table + readable family name."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
from fontTools.ttLib import TTFont, newTable

BASE = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg"
SRC = os.path.join(BASE, "02-assets", "fonts", "DKSPPM+Assassin$.ttf")
DST = os.path.join(BASE, "02-assets", "fonts-web", "assassin2.ttf")

tt = TTFont(SRC)
print("tables:", sorted(tt.keys()))
print("unitsPerEm:", tt["head"].unitsPerEm, "numGlyphs:", tt["maxp"].numGlyphs)
if "post" in tt:
    print("post fmt:", tt["post"].formatType, "italic:", getattr(tt["post"], "italicAngle", None))

post = tt["post"]
if getattr(post, "italicAngle", None) is None:
    post.italicAngle = 0
print("kept post, italic:", post.italicAngle, "fmt:", post.formatType)

fam = "AssassinDisplay"
for rec in list(tt["name"].names):
    if rec.nameID in (1, 4):
        rec.string = fam
    elif rec.nameID == 6:
        rec.string = fam
    elif rec.nameID == 2:
        rec.string = "Regular"

if "OS/2" not in tt:
    print("WARNING: no OS/2")
else:
    tt["OS/2"].usWeightClass = 400
    tt["OS/2"].fsSelection = 0x40
    print("OS/2 ok")

tt.save(DST)
tt.close()
print("saved", DST, os.path.getsize(DST))

# verify
v = TTFont(DST)
print("verify tables:", sorted(v.keys()))
cm = v.getBestCmap()
print("cmap:", len(cm), "".join(sorted(chr(c) for c in cm))[:80])
print("name:", v["name"].getDebugName(1), "| post italic:", v["post"].italicAngle)
v.close()
