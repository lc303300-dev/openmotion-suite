# -*- coding: utf-8 -*-
import json, sys, os
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open(os.path.join(os.path.dirname(__file__), "pdf_dump.json"), encoding="utf-8"))
p = d["items"][0]
print("page", p["rect"], "rotation", p["rotation"])
print("--- TEXT (top to bottom) ---")
for t in sorted(p["text"], key=lambda x: (round(x["bbox"][1]), x["bbox"][0])):
    print(f"{t['color']} sz={t['size']:5.1f} {t['font'][:36]:36s} bbox={t['bbox']} origin={t['origin']} | {t['text']}")
print("--- IMAGES ---")
for im in p["images"]:
    print(im)
print("--- XREFS ---")
for x in p["xrefs"]:
    print(x)
print("--- DRAWS ---")
for dr in p["draws"]:
    print(dr)
print("--- DRAW SUMMARY ---")
print(json.dumps(p["draw_summary"], ensure_ascii=False, indent=1))
