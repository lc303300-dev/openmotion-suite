# -*- coding: utf-8 -*-
"""Add post table, readable names, verify glyph outlines, and render a proof image."""
import sys, os, re
sys.stdout.reconfigure(encoding="utf-8")
import fitz
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable

BASE = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg"
FNT = os.path.join(BASE, "02-assets", "fonts")
OUT = os.path.join(BASE, "02-assets", "fonts-web")

JOBS = [
    ("QGGUPM+HarmonyOS_Sans_SC_Medium.ttf", "hos-medium.ttf", "HarmonyOS Sans SC Medium", 500),
    ("IXDTHC+HarmonyOS_Sans_SC_Light.ttf", "hos-light.ttf", "HarmonyOS Sans SC Light", 300),
]


def parse_tounicode(t):
    m = {}
    for blk in re.findall(r"beginbfchar(.*?)endbfchar", t, re.S):
        for s, d in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
            m[int(s, 16)] = "".join(chr(int(d[i:i + 4], 16)) for i in range(0, len(d), 4))
    for blk in re.findall(r"beginbfrange(.*?)endbfrange", t, re.S):
        for lo, hi, d in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
            for k in range(int(lo, 16), int(hi, 16) + 1):
                m[k] = chr(int(d, 16) + k - int(lo, 16))
    return m


doc = fitz.open(r"F:\LiuCan\Work\20261123-JMHB\画板 16(1).pdf")
tu_map = {}
for f in doc.get_page_fonts(0):
    base = f[3]
    tu = doc.xref_get_key(f[0], "ToUnicode")
    if tu and tu[0] == "xref":
        tu_map[base] = parse_tounicode(doc.xref_stream(int(tu[1].split()[0])).decode("latin-1", "ignore"))
doc.close()

for src, dst, family, weight in JOBS:
    base = src.rsplit(".", 1)[0]
    tt = TTFont(os.path.join(FNT, src))
    order = tt.getGlyphOrder()
    cmap_tbl = {}
    for code, uni in tu_map[base].items():
        if code < len(order):
            cmap_tbl[ord(uni)] = order[code]

    tbl = newTable("cmap")
    tbl.tableVersion = 0
    sub = CmapSubtable.newSubtable(4)
    sub.platformID, sub.platEncID, sub.language = 3, 1, 0
    sub.cmap = cmap_tbl
    tbl.tables = [sub]
    tt["cmap"] = tbl

    # post
    post = newTable("post")
    post.formatType = 3.0
    post.italicAngle = 0
    post.underlinePosition = -100
    post.underlineThickness = 50
    post.isFixedPitch = 0
    post.minMemType42 = 0
    post.maxMemType42 = 0
    post.minMemType1 = 0
    post.maxMemType1 = 0
    tt["post"] = post

    # readable names
    name = tt["name"]
    for rec in list(name.names):
        if rec.nameID == 1:
            rec.string = family
        elif rec.nameID == 4:
            rec.string = family
        elif rec.nameID == 6:
            rec.string = family.replace(" ", "-")
    tt["OS/2"].usWeightClass = weight
    tt["OS/2"].usWinAscent = 1069
    tt["OS/2"].usWinDescent = 271

    # verify outlines for the characters we need
    glyf = tt["glyf"]
    missing = []
    for ch in "武汉小学武珞路中学双本部名校为邻让成长拥有更确定的归处":
        gname = cmap_tbl.get(ord(ch))
        if not gname:
            missing.append((ch, "no-cmap"))
            continue
        g = glyf[gname]
        if g.numberOfContours == 0:
            missing.append((ch, "empty"))
    print(f"{dst}: cmap={len(cmap_tbl)} missing/empty={missing or 'none'}")

    out = os.path.join(OUT, dst)
    tt.save(out)
    tt.close()
    print("  saved", out, os.path.getsize(out), "bytes")
