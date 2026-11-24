# -*- coding: utf-8 -*-
"""Dump all drawings and the raw content stream to locate the stamp pattern."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
import fitz

SRC = r"F:\LiuCan\Work\20261123-JMHB\画板 16(1).pdf"
BASE = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg"
doc = fitz.open(SRC)
page = doc[0]

print("=== ALL DRAWINGS (extended) ===")
for i, d in enumerate(page.get_drawings(extended=True)):
    print(i, "type=", d.get("type"), "fill=", d.get("fill"), "color=", d.get("color"),
          "w=", d.get("width"), "rect=", [round(v, 1) for v in d.get("rect", [])],
          "nitems=", len(d.get("items", [])), "seqno=", d.get("seqno"), "layer=", d.get("layer"))

print("\n=== CONTENT STREAM ===")
cont = b"".join(doc.xref_stream(x) for x in page.get_contents())
open(os.path.join(BASE, "03-work", "content.bin"), "wb").write(cont)
print(cont.decode("latin-1"))

print("\n=== SHADINGS / PATTERNS ===")
for xref in range(1, doc.xref_length()):
    try:
        o = doc.xref_object(xref, compressed=True)
    except Exception:
        continue
    if "/Shading" in o or "/PatternType" in o:
        print(xref, o[:400].replace("\n", " "))
doc.close()
