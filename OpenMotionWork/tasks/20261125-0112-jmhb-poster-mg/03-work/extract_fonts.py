# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
import fitz
SRC = r"F:\LiuCan\Work\20261123-JMHB\画板 16(1).pdf"
FNT = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg\02-assets\fonts"
os.makedirs(FNT, exist_ok=True)
doc = fitz.open(SRC)
for f in doc.get_page_fonts(0):
    xref = f[0]; ext = f[1]; typ = f[2]; base = f[3]
    try:
        name, fext, ftype, buf = doc.extract_font(xref)
        out = os.path.join(FNT, f"{base}.{fext}")
        open(out, "wb").write(buf)
        print("OK", xref, base, fext, ftype, len(buf), out)
    except Exception as e:
        print("FAIL", xref, base, e)
doc.close()
