# -*- coding: utf-8 -*-
"""Extract per-character positions for every text run into text-layout.json."""
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8")
import fitz

SRC = r"F:\LiuCan\Work\20261123-JMHB\画板 16(1).pdf"
BASE = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg"
doc = fitz.open(SRC)
page = doc[0]

runs = []
for sp in page.get_texttrace():
    chars = []
    for c in sp["chars"]:
        uni, gid, origin, bbox = c[0], c[1], c[2], c[3]
        chars.append({"ch": chr(uni), "x": round(origin[0], 3), "y": round(origin[1], 3),
                      "gid": gid})
    runs.append({
        "font": sp["font"], "size": round(sp["size"], 3), "color": sp["color"],
        "type": sp["type"], "chars": chars,
    })

json.dump(runs, open(os.path.join(BASE, "03-work", "text-trace.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

for r in runs:
    txt = "".join(c["ch"] for c in r["chars"])
    print(f'{r["font"]:28s} size={r["size"]:7.3f} n={len(r["chars"]):3d} {txt!r}')
    print("   xs:", [c["x"] for c in r["chars"]][:14], "..." if len(r["chars"]) > 14 else "")
doc.close()
