# -*- coding: utf-8 -*-
"""Probe the source PDF: page geometry, text spans, images, vector fills."""
import json, sys, os
import fitz

SRC = r"F:\LiuCan\Work\20261123-JMHB\画板 16(1).pdf"
OUT = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg\03-work"

doc = fitz.open(SRC)
report = {"path": SRC, "pages": doc.page_count, "meta": doc.metadata, "items": []}

for pno in range(doc.page_count):
    page = doc[pno]
    info = {"page": pno, "rect": list(page.rect), "rotation": page.rotation,
            "text": [], "images": [], "draws": []}
    d = page.get_text("dict")
    for b in d.get("blocks", []):
        if b.get("type") == 0:
            for line in b.get("lines", []):
                for sp in line.get("spans", []):
                    info["text"].append({
                        "text": sp["text"],
                        "font": sp["font"],
                        "size": round(sp["size"], 2),
                        "color": "#%06x" % sp["color"],
                        "bbox": [round(v, 2) for v in sp["bbox"]],
                        "origin": [round(v, 2) for v in sp["origin"]],
                        "flags": sp["flags"],
                    })
        elif b.get("type") == 1:
            info["images"].append({"bbox": [round(v, 2) for v in b["bbox"]],
                                   "width": b.get("width"), "height": b.get("height"),
                                   "ext": b.get("ext")})
    # vector fills
    fills = {}
    for dr in page.get_drawings():
        key = (dr.get("fill"), dr.get("color"), round(dr.get("width") or 0, 2))
        fills[str(key)] = fills.get(str(key), 0) + 1
        info["draws"].append({"type": dr.get("type"),
                              "fill": dr.get("fill"), "color": dr.get("color"),
                              "width": dr.get("width"),
                              "rect": [round(v, 2) for v in dr["rect"]]})
    info["draw_summary"] = fills
    # image xrefs actually on page
    info["xrefs"] = [{"xref": im[0], "w": im[2], "h": im[3], "cs": im[5]} for im in page.get_images(full=True)]
    report["items"].append(info)

# font list
report["fonts"] = []
for pno in range(doc.page_count):
    for f in doc.get_page_fonts(pno):
        e = {"page": pno, "xref": f[0], "ext": f[1], "type": f[2], "basefont": f[3]}
        if e not in report["fonts"]:
            report["fonts"].append(e)

with open(os.path.join(OUT, "pdf_dump.json"), "w", encoding="utf-8") as fh:
    json.dump(report, fh, ensure_ascii=False, indent=1)

print("pages:", doc.page_count)
for it in report["items"]:
    print("page", it["page"], "rect", it["rect"], "rot", it["rotation"],
          "texts", len(it["text"]), "images", len(it["images"]), "draws", len(it["draws"]))
print("fonts:", json.dumps(report["fonts"], ensure_ascii=False))

# render page images: full page + 3x zoom
for pno in range(doc.page_count):
    page = doc[pno]
    for tag, zoom in (("1x", 1.0), ("3x", 3.0)):
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        name = os.path.join(OUT, f"page{pno+1}_{tag}.png")
        pix.save(name)
        print("saved", name, pix.width, "x", pix.height)
doc.close()
