# -*- coding: utf-8 -*-
"""Rebuild cmap (v2) + dump CFF glyph outlines safely."""
import sys, os, re, json, traceback
sys.stdout.reconfigure(encoding="utf-8")
import fitz
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable

BASE = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg"
SRC = r"F:\LiuCan\Work\20261123-JMHB\鐢绘澘 16(1).pdf"
FNT = os.path.join(BASE, "02-assets", "fonts")
OUT = os.path.join(BASE, "02-assets", "web")
os.makedirs(OUT, exist_ok=True)
doc = fitz.open(SRC)

def parse_tounicode(cmap_text):
    m = {}
    for blk in re.findall(r"beginbfchar(.*?)endbfchar", cmap_text, re.S):
        for src, dst in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
            m[int(src, 16)] = "".join(chr(int(dst[i:i + 4], 16)) for i in range(0, len(dst), 4))
    for blk in re.findall(r"beginbfrange(.*?)endbfrange", cmap_text, re.S):
        for lo, hi, dst in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
            for k in range(int(lo, 16), int(hi, 16) + 1):
                m[k] = chr(int(dst, 16) + k - int(lo, 16))
    return m

for f in doc.get_page_fonts(0):
    xref, base = f[0], f[3]
    tu = doc.xref_get_key(xref, "ToUnicode")
    c2g = doc.xref_get_key(xref, "CIDToGIDMap")
    print(f"--- {base}\n    ToUnicode={tu}  CIDToGIDMap={c2g}")
    if not (tu and tu[0] == "xref"):
        continue
    text = doc.xref_stream(int(tu[1].split()[0])).decode("latin-1", "ignore")
    m = parse_tounicode(text)
    print("    map sample:", {k: v for k, v in list(m.items())[:6]})

    path = os.path.join(FNT, base + ".ttf")
    if not os.path.exists(path):
        continue
    tt = TTFont(path)
    order = tt.getGlyphOrder()
    if c2g[0] == "xref":
        raw = doc.xref_stream(int(c2g[1].split()[0]))
        import struct
        cid2gid = list(struct.unpack(">%dH" % (len(raw) // 2), raw))
        print("    CIDToGIDMap stream bytes:", len(raw))
    else:
        cid2gid = None
    cmap_tbl = {}
    for code, uni in m.items():
        gid = code if cid2gid is None else cid2gid[code]
        if 0 <= gid < len(order):
            cmap_tbl[ord(uni)] = order[gid]
    tbl = newTable("cmap")
    tbl.tableVersion = 0
    sub = CmapSubtable.newSubtable(4)
    sub.platformID, sub.platEncID, sub.language = 3, 1, 0
    sub.cmap = cmap_tbl
    tbl.tables = [sub]
    tt["cmap"] = tbl
    out = os.path.join(OUT, base + ".ttf")
    tt.save(out)
    print("    rebuilt ->", out, len(cmap_tbl), "entries:", "".join(cmap_tbl_char := [k for k in map(chr, sorted(cmap_tbl))]))
    tt.close()

# ---- CFF
print("\n=== CFF ===")
try:
    from fontTools.cffLib import CFFFontSet
    from fontTools.misc.psCharStrings import T2CharStringPen
    with open(os.path.join(FNT, "SRIBRI+BoteraTFE-Regular.cff"), "rb") as fh:
        cff = CFFFontSet()
        cff.decompile(fh, None)
    print("fonts:", cff.fontNames)
    name = cff.fontNames[0]
    td = cff[name]
    print("FontMatrix:", td.rawDict.get("FontMatrix"), "| CharStrings:", len(td.CharStrings))
    names = list(td.CharStrings.keys())
    print("glyph names:", names[:40])
    glyphset = td.CharStrings
    out_json = {}
    for nm in names:
        cs = glyphset[nm]
        pen = T2CharStringPen(None, glyphSet=glyphset)
        cs.draw(pen)
        out_json[nm] = {"path": pen.getCommands(), "width": getattr(cs, "width", None)}
        print(f"  {nm}: w={getattr(cs,'width',None)} len={len(pen.getCommands())}")
    with open(os.path.join(OUT, "botera_glyphs.json"), "w", encoding="utf-8") as fh:
        json.dump(out_json, fh, ensure_ascii=False)
    print("saved botera_glyphs.json")
except Exception:
    traceback.print_exc()
doc.close()

