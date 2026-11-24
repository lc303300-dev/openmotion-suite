# -*- coding: utf-8 -*-
"""Trace per-glyph positions; hunt the gold stamp (inline image / XObject / pattern)."""
import sys, os, re, json
sys.stdout.reconfigure(encoding="utf-8")
import fitz

BASE = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg"
SRC = r"F:\LiuCan\Work\20261123-JMHB\画板 16(1).pdf"
OUT = os.path.join(BASE, "03-work")

doc = fitz.open(SRC)
page = doc[0]

# ---- per-glyph trace
trace = page.get_texttrace()
print("=== TEXT TRACE (spans) ===")
for sp in trace:
    chars = sp["chars"]
    txt = "".join(chr(c[0]) for c in chars)
    print(f"font={sp['font']} size={sp['size']:.2f} color={sp['color']} type={sp['type']} text={txt!r}")
    xs = []
    for c in chars:
        uni, gid, origin, bbox = c[0], c[1], c[2], c[3]
        xs.append((chr(uni), round(origin[0], 2), round(origin[1], 2), round(bbox[0], 2), round(bbox[2], 2)))
    print("   chars:", xs)

# ---- content stream tokens
cont = b"".join(doc.xref_stream(x) for x in page.get_contents())
print("\n=== CONTENT STREAM ===", len(cont), "bytes")
for tok in [b"BI", b"ID", b"EI", b"Do", b"sh", b"SCN", b"scn", b"re", b"f*", b"W*", b"BX", b"BDC", b"EMC"]:
    print(f"  {tok.decode()}: {cont.count(tok)}")
# find inline image blocks
for m in re.finditer(rb"BI\s", cont):
    seg = cont[m.start():m.start() + 260]
    print("INLINE IMG:", seg[:200])
    break

# form xobjects
print("\n=== XOBJECTS ===")
for xo in page.get_xobjects():
    print("  ", xo)
    try:
        info = doc.xref_object(xo[0])
        print("    dict:", info[:300].replace("\n", " "))
    except Exception as e:
        print("    ", e)

# drawings extended
print("\n=== get_drawings(extended) ===")
dr = page.get_drawings(extended=True)
print("count:", len(dr))
for d in dr:
    if d.get("fill") and d["fill"][0] > 0.3 and abs(d["fill"][0] - 0.349) > 0.02:
        print("  fill", d["fill"], "rect", [round(v, 1) for v in d["rect"]], "type", d["type"], "items", len(d.get("items", [])))

# ---- big render of stamp area
clip = fitz.Rect(30, 620, 230, 830)
pix = page.get_pixmap(matrix=fitz.Matrix(8, 8), clip=clip, alpha=False)
pix.save(os.path.join(OUT, "stamp_8x.png"))
print("\nstamp_8x:", pix.width, pix.height)

clip2 = fitz.Rect(0, 0, 720, 1280)
pix2 = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=clip2, alpha=False)
pix2.save(os.path.join(OUT, "page_2x.png"))
doc.close()
