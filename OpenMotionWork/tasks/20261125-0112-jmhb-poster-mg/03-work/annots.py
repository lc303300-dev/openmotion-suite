# -*- coding: utf-8 -*-
"""Inspect page annotations (likely holds the gold stamp)."""
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8")
import fitz

SRC = r"F:\LiuCan\Work\20261123-JMHB\画板 16(1).pdf"
BASE = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg"
doc = fitz.open(SRC)
page = doc[0]
annots = list(page.annots() or [])
print("annotations:", len(annots))
for a in annots:
    print("---")
    print(" type:", a.type, "| rect:", a.rect, "| opacity:", a.opacity,
          "| colors:", a.colors, "| info:", a.info)
    print(" xref:", a.xref)
    try:
        print(" obj:", doc.xref_object(a.xref)[:1200].replace("\n", " "))
    except Exception as e:
        print(" obj fail", e)

# also widgets / form fields
print("\nwidgets:", list(page.widgets() or [])[:3])
print("pdf layers:", doc.layer_ui_configs() if hasattr(doc, "layer_ui_configs") else "n/a")

# what does render_page say about annots?
print("\nrender default annots:", page.get_pixmap().width)

# render without annotations for comparison
pix_no = page.get_pixmap(matrix=fitz.Matrix(4, 4), annots=False)
pix_no.save(os.path.join(BASE, "03-work", "page_noannots.png"))
pix_yes = page.get_pixmap(matrix=fitz.Matrix(4, 4), annots=True)
pix_yes.save(os.path.join(BASE, "03-work", "page_annots.png"))
print("saved annots compare")
doc.close()
