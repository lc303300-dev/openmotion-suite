# -*- coding: utf-8 -*-
"""1) Rebuild HarmonyOS cmap from PDF ToUnicode; 2) dump BoteraTFE CFF glyph paths."""
import sys, os, re, json
sys.stdout.reconfigure(encoding="utf-8")
import fitz
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

BASE = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg"
SRC = r"F:\LiuCan\Work\20261123-JMHB\画板 16(1).pdf"
FNT = os.path.join(BASE, "02-assets", "fonts")
OUT = os.path.join(BASE, "02-assets", "web")
os.makedirs(OUT, exist_ok=True)

doc = fitz.open(SRC)
page = doc[0]

# ---------- 1. ToUnicode maps ----------
def parse_tounicode(cmap_text):
    """Return {code:int -> str} from a ToUnicode CMap."""
    m = {}
    for blk in re.findall(r"beginbfchar(.*?)endbfchar", cmap_text, re.S):
        for src, dst in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
            m[int(src, 16)] = "".join(chr(int(dst[i:i + 4], 16)) for i in range(0, len(dst), 4))
    for blk in re.findall(r"beginbfrange(.*?)endbfrange", cmap_text, re.S):
        for lo, hi, dst in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
            lo_i, hi_i = int(lo, 16), int(hi, 16)
            base = int(dst, 16)
            for k in range(lo_i, hi_i + 1):
                m[k] = chr(base + k - lo_i)
    return m

font_map = {}
for f in doc.get_page_fonts(0):
    xref, ext, typ, base = f[0], f[1], f[2], f[3]
    tu = doc.xref_get_key(xref, "ToUnicode")
    if tu and tu[0] == "xref":
        objno = int(tu[1].split()[0])
        text = doc.xref_stream(objno).decode("latin-1", "ignore")
        m = parse_tounicode(text)
        font_map[base] = m
        print(f"{base}: ToUnicode entries={len(m)}")
    else:
        print(f"{base}: no ToUnicode ({tu})")

# ---------- 2. rebuild cmap for HarmonyOS ----------
for base, m in font_map.items():
    path = os.path.join(FNT, base + ".ttf")
    if not os.path.exists(path):
        continue
    f = TTFont(path)
    gid_order = f.getGlyphOrder()
    # CID == GID assumed (Identity CIDToGIDMap) for these subset fonts
    cmap_tbl = {}
    for code, uni in m.items():
        if code < len(gid_order):
            cmap_tbl[ord(uni)] = gid_order[code]
    from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
    sub = CmapSubtable.newSubtable(4)
    sub.platformID, sub.platEncID, sub.language = 3, 1, 0
    sub.cmap = cmap_tbl
    f["cmap"] = f["cmap"] if "cmap" in f else None
    f["cmap"] = __import__("fontTools.ttLib.tables._c_m_a_p", fromlist=["table__c_m_a_p"]).table__c_m_a_p()
    f["cmap"].tables = [sub]
    out = os.path.join(OUT, base + ".ttf")
    f.save(out)
    print("rebuilt cmap ->", out, "entries", len(cmap_tbl))
    # verify needed chars
    need = "武汉小学武珞路中学双本部名校为邻让成长拥有更确定的归处"
    miss = [c for c in need if ord(c) not in cmap_tbl]
    print("   missing CN:", "".join(miss) or "NONE")
    f.close()

# ---------- 3. BoteraTFE CFF paths ----------
cff_path = os.path.join(FNT, "SRIBRI+BoteraTFE-Regular.cff")
try:
    from fontTools.cffLib import CFFFontSet
    from fontTools.misc.psCharStrings import T2CharStringPen
    cff = CFFFontSet()
    with open(cff_path, "rb") as fh:
        cff.decompile(fh, None)
    td = cff[cff.fontNames[0]]
    print("\nCFF font:", cff.fontNames[0], "| topDict", td.rawDict.get("FontMatrix"))
    print("glyph count:", len(td.CharStrings))
    names = list(td.CharStrings.keys())
    print("glyph names:", names)
    upm = td.FontMatrix[0] * 1000 if td.FontMatrix else 1000
    print("unitsPerEm:", td.rawDict.get("FontMatrix"))
    for nm in names:
        cs = td.CharStrings[nm]
        pen = T2CharStringPen(None, glyphSet=td.CharStrings)  # width=None keeps original
        cs.draw(pen)
        path = pen.getCommands()
        width = getattr(cs, "width", None)
        print(f"  {nm}: width={width} pathlen={len(path)}")
        print("   ", path[:120])
    doc.close()
except Exception as e:
    import traceback; traceback.print_exc()
doc.close()
