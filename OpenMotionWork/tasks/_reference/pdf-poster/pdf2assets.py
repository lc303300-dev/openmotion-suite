# -*- coding: utf-8 -*-
"""pdf2assets.py — PDF 画板 → 可复刻素材包（一次跑完，避免逐项试错）。

用法:
    python pdf2assets.py <poster.pdf> <outdir> [--scale 1.5] [--page 0] [--no-images]

产出:
    outdir/orig/            内嵌位图原样（带 smask 的已合成为 PNG alpha）
    outdir/images/          按 --scale 放大的上屏素材（.jpg q94 / .png）
    outdir/fonts/*.ttf      可直接导入 OpenMotion 的字体（cmap 重建 + post 补全 + 名称清洗）
    outdir/fonts/glyphs-*.json   CFF 轮廓字形的 SVG path（如 BoteraTFE 这类）
    outdir/trace.json       逐字位置（font/size/color/x/y）
    outdir/matrix.json      每个图像实例的 y-down 矩阵 + CSS 像素矩阵 + 框内嵌套矩阵
    outdir/report.md        人读摘要（页尺寸/底色/字体覆盖/图像清单/文字行）

依赖: PyMuPDF、fontTools、Pillow、numpy（后两者仅用于放大）

为什么要有这个脚本（血泪版）：
  1. PDF 里的图片不一定是"摆正的"——可能是 90° 旋转、甚至带斜切（两轴夹角 ≠ 90°），
     用 rotate+scale 反推会错；必须原样搬 matrix。
  2. 中文子集 ttf 的 cmap 通常是空的（PDF 用 CID 编码 + ToUnicode），
     直接导入 OpenMotion 会失败或渲染成豆腐。
  3. 子集字体常缺 post 表，OpenMotion 读 italicAngle 会抛 "Cannot read properties of undefined"。
  4. 字体名里的 `$`、`+`（子集前缀）会让渲染端加载失败。
  5. PNG 素材在 PDF 里往往是"黑底 + 软蒙版"，直接导出会得到一块黑。
"""
from __future__ import annotations

import io
import json
import math
import os
import re
import sys

import fitz
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None


# ---------------------------------------------------------------- 矩阵工具
# PDF 内容流里的 cm 是 y 向上（原点左下），fitz/浏览器是 y 向下（原点左上）。
# 且 PDF 图像在 unit square 里 v 向上，栅格数据 v 向下，所以还要再做一次 v 翻转。
# 正确换算（实测对齐 fitz 的 get_image_info().transform）：
def pdf_cm_to_fitz(a, b, c, d, e, f, page_h):
    """content stream 的 cm -> fitz 的 y-down、左上原点的 unit 矩阵。"""
    return (a, -b, -c, d, c + e, page_h - d - f)


def unit_to_pixels(m, w, h):
    """unit(0..1) 矩阵 -> 作用在 WxH 像素元素上的 CSS matrix。"""
    a, b, c, d, e, f = m
    return (a / w, b / w, c / h, d / h, e, f)


def mat_mul(A, B):
    a1, b1, c1, d1, e1, f1 = A
    a2, b2, c2, d2, e2, f2 = B
    return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2,
            a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)


def mat_inv(m):
    a, b, c, d, e, f = m
    det = a * d - b * c
    ia, ib, ic, id_ = d / det, -b / det, -c / det, a / det
    return (ia, ib, ic, id_, -(ia * e + ic * f), -(ib * e + id_ * f))


def css(m):
    return "matrix(" + ",".join(f"{v:.7f}" for v in m) + ")"


def analyze(m):
    """返回视觉尺寸、两轴角度、行列式符号（负=镜像）、是否斜切。"""
    a, b, c, d, e, f = m
    uw, vh = math.hypot(a, b), math.hypot(c, d)
    uang, vang = math.degrees(math.atan2(b, a)), math.degrees(math.atan2(d, c))
    det = a * d - b * c
    skew = (vang - uang) % 360
    return {
        "u_len": round(uw, 3), "v_len": round(vh, 3),
        "u_deg": round(uang, 3), "v_deg": round(vang, 3),
        "axis_angle": round(skew, 3),
        "mirrored": det < 0,
        "sheared": abs(((skew % 180) - 90)) > 0.8,
    }


def corners(m):
    a, b, c, d, e, f = m
    return [(a * u + c * v + e, b * u + d * v + f)
            for u, v in ((0, 0), (1, 0), (0, 1), (1, 1))]


def shadow_for(m, dist=9.0, blur=19.0, color="rgba(89,87,87,0.30)"):
    """PDF 的投影是"页面坐标向下"的；把页面 (0,1) 转进元素本地坐标，
    再除以元素自身缩放，得到 box-shadow 的本地偏移。"""
    a, b, c, d, e, f = m
    det = a * d - b * c
    lx, ly = -c / det, a / det
    n = math.hypot(lx, ly) or 1.0
    scale = math.hypot(a, b) or 1.0
    d2, b2 = dist / scale, blur / scale
    return f"{lx / n * d2:.2f}px {ly / n * d2:.2f}px {b2:.1f}px {color}"


# ---------------------------------------------------------------- 字体
def parse_tounicode(text):
    m = {}
    for blk in re.findall(r"beginbfchar(.*?)endbfchar", text, re.S):
        for s, d in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
            m[int(s, 16)] = "".join(chr(int(d[i:i + 4], 16)) for i in range(0, len(d), 4))
    for blk in re.findall(r"beginbfrange(.*?)endbfrange", text, re.S):
        for lo, hi, d in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
            for k in range(int(lo, 16), int(hi, 16) + 1):
                m[k] = chr(int(d, 16) + k - int(lo, 16))
    return m


def clean_family(basefont):
    name = basefont
    if re.match(r"^[A-Z]{6}\+", name):          # 去掉 ABCDEF+ 子集前缀
        name = name[7:]
    name = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_")
    return name or "SubsetFace"


def repair_ttf(src_path, cmap_pairs, family, weight=400, out_path=None):
    """补 cmap / post 表并把 family 改成纯 ASCII，返回可用 ttf 路径。"""
    tt = TTFont(src_path)
    order = tt.getGlyphOrder()

    table = newTable("cmap")
    table.tableVersion = 0
    sub = CmapSubtable.newSubtable(4)
    sub.platformID, sub.platEncID, sub.language = 3, 1, 0
    sub.cmap = {}
    for code, uni in cmap_pairs.items():
        if 0 <= code < len(order):
            sub.cmap[ord(uni)] = order[code]
    table.tables = [sub]
    tt["cmap"] = table

    # 缺 post 表时 OpenMotion 读 italicAngle 会崩；保留已有表，缺了才补。
    if "post" not in tt:
        post = newTable("post")
        post.formatType, post.italicAngle = 3.0, 0
        post.underlinePosition, post.underlineThickness = -100, 50
        post.isFixedPitch = 0
        post.minMemType42 = post.maxMemType42 = 0
        post.minMemType1 = post.maxMemType1 = 0
        tt["post"] = post
    else:
        if getattr(tt["post"], "italicAngle", None) is None:
            tt["post"].italicAngle = 0

    for rec in list(tt["name"].names):
        if rec.nameID in (1, 4):
            rec.string = family
        elif rec.nameID == 6:
            rec.string = family
        elif rec.nameID == 2:
            rec.string = "Regular"
    if "OS/2" in tt:
        tt["OS/2"].usWeightClass = weight

    out_path = out_path or src_path
    tt.save(out_path)
    n = len(sub.cmap)
    tt.close()
    return out_path, n


def cff_glyph_paths(cff_bytes):
    """CID/Type1 CFF -> {glyph: {path, width}}（SVG path，y 向上，1000upm）。"""
    from fontTools.cffLib import CFFFontSet
    from fontTools.pens.svgPathPen import SVGPathPen

    cff = CFFFontSet()
    cff.decompile(io.BytesIO(cff_bytes), None)   # 必须传 BytesIO：文件一关就 seek 失败
    td = cff[cff.fontNames[0]]
    glyphset = td.CharStrings
    out = {}
    for nm in glyphset.keys():
        cs = glyphset[nm]
        pen = SVGPathPen(glyphset)
        cs.draw(pen)
        out[nm] = {"path": pen.getCommands(), "width": getattr(cs, "width", None)}
    return out


# ---------------------------------------------------------------- 位图
def image_with_mask(doc, xref):
    info = doc.extract_image(xref)
    img = Image.open(io.BytesIO(info["image"])) if Image else None
    sm = info.get("smask", 0)
    if img is not None and sm:
        mi = doc.extract_image(sm)
        mask = Image.open(io.BytesIO(mi["image"])).convert("L")
        img = img.convert("RGBA")
        if mask.size != img.size:
            mask = mask.resize(img.size, Image.LANCZOS)
        img.putalpha(mask)
    return info, img


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    src, outdir = argv[1], argv[2]
    scale, page_no, do_images = 1.5, 0, True
    for i, a in enumerate(argv[3:], start=3):
        if a == "--scale":
            scale = float(argv[i + 1])
        elif a == "--page":
            page_no = int(argv[i + 1])
        elif a == "--no-images":
            do_images = False

    for sub in ("orig", "images", "fonts"):
        os.makedirs(os.path.join(outdir, sub), exist_ok=True)

    doc = fitz.open(src)
    page = doc[page_no]
    H = page.rect.height
    report = [f"# {os.path.basename(src)} → 素材包", ""]
    report.append(f"- 页面: {page.rect.width:.1f} × {H:.1f} pt（{page.rotation}°）")

    # ---- 底色（最大面积的纯色填充）
    area_fill = {}
    for d in page.get_drawings():
        if d.get("fill") and abs(d["rect"].width * d["rect"].height) > 0:
            key = tuple(round(v, 3) for v in d["fill"])
            area_fill[key] = area_fill.get(key, 0) + d["rect"].width * d["rect"].height
    if area_fill:
        top = max(area_fill.items(), key=lambda kv: kv[1])[0]
        hexc = "#%02X%02X%02X" % tuple(int(round(v * 255)) for v in top)
        report.append(f"- 主底色填充: {hexc}  rgb{top}")
    report.append("")

    # ---- 图像实例（顺序即绘制顺序 = z 序）
    images = []
    infos = page.get_image_info()
    report.append(f"## 图像实例 ({len(infos)})")
    for idx, inst in enumerate(infos):
        m = tuple(inst["transform"])
        an = analyze(m)
        cs_ = corners(m)
        xs = [p[0] for p in cs_]
        ys = [p[1] for p in cs_]
        bbox = [round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2)]
        cx, cy = sum(xs) / 4, sum(ys) / 4
        pw, ph = inst["width"], inst["height"]
        entry = {
            "index": idx,
            "pixel": [pw, ph],
            "unit": [round(v, 7) for v in m],
            "css": [round(v, 7) for v in unit_to_pixels(m, pw, ph)],
            "bbox": bbox,
            "center": [round(cx, 3), round(cy, 3)],
            "visual": [an["u_len"], an["v_len"]],
            "u_deg": an["u_deg"], "v_deg": an["v_deg"],
            "mirrored": an["mirrored"], "sheared": an["sheared"],
            "css_string": css(unit_to_pixels(m, pw, ph)),
            "box_shadow": shadow_for(unit_to_pixels(m, pw, ph)),
        }
        images.append(entry)
        flag = " sheared" if an["sheared"] else ""
        flag += " mirrored" if an["mirrored"] else ""
        report.append(f"{idx:02d}. {pw}×{ph} bbox={bbox} 视觉={an['u_len']:.1f}×{an['v_len']:.1f}"
                      f" u={an['u_deg']:.2f}° v={an['v_deg']:.2f}°{flag}")
    report.append("")

    # ---- 导出位图
    if do_images and Image is not None:
        exported = {}
        for xref, w, h, cs in [(im[0], im[2], im[3], im[5]) for im in page.get_images(full=True)]:
            info, img = image_with_mask(doc, xref)
            if img is None:
                continue
            ext = "png" if info.get("smask") else (info.get("ext") or "png")
            orig = os.path.join(outdir, "orig", f"xref{xref:03d}_{w}x{h}.{ext}")
            (img.convert("RGBA") if ext == "png" else img.convert("RGB")).save(orig)
            big = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
            dst = os.path.join(outdir, "images", f"xref{xref:03d}.{'png' if ext == 'png' else 'jpg'}")
            if ext == "png":
                big.save(dst)
            else:
                big.convert("RGB").save(dst, quality=94, subsampling=0)
            exported[xref] = {"orig": orig, "screen": dst,
                              "has_alpha": bool(info.get("smask")), "size": [w, h]}
        report.append(f"## 位图\n导出 {len(exported)} 张到 orig/ 与 images/（×{scale}）")
        report.append("")

    # ---- 字体
    fonts = []
    report.append("## 字体")
    for f in doc.get_page_fonts(page_no):
        xref, ext, typ, base = f[0], f[1], f[2], f[3]
        tu = doc.xref_get_key(xref, "ToUnicode")
        pairs = {}
        if tu and tu[0] == "xref":
            cmap_text = doc.xref_stream(int(tu[1].split()[0])).decode("latin-1", "ignore")
            pairs = parse_tounicode(cmap_text)
        glyphs = None
        try:
            name, fext, ftype, buf = doc.extract_font(xref)
        except Exception as exc:
            report.append(f"- {base}: 提取失败 {exc}")
            continue
        family = clean_family(base)
        entry = {"basefont": base, "family": family, "ext": fext, "type": ftype,
                 "unicode_codes": len(pairs), "file": None, "glyph_json": None}
        raw = os.path.join(outdir, "fonts", f"{family}.{fext}")
        with open(raw, "wb") as fh:
            fh.write(buf)
        if fext in ("ttf", "otf") and pairs:
            out = os.path.join(outdir, "fonts", f"{family}.ttf")
            try:
                out, n = repair_ttf(raw, pairs, family)
                entry["file"] = out
                entry["cmap_entries"] = n
                report.append(f"- {base} → {family}.ttf（cmap {n} 项，可导入）")
            except Exception as exc:
                report.append(f"- {base}: 修字体失败 {exc}")
        elif fext in ("cff", "cid") or ftype in ("Type1", "CIDFontType0"):
            try:
                glyphs = cff_glyph_paths(buf)
                gp = os.path.join(outdir, "fonts", f"glyphs-{family}.json")
                with open(gp, "w", encoding="utf-8") as fh:
                    json.dump(glyphs, fh, ensure_ascii=False)
                entry["glyph_json"] = gp
                report.append(f"- {base} → glyphs-{family}.json（{len(glyphs)} 个轮廓字形，内联 SVG 用）")
            except Exception as exc:
                report.append(f"- {base}: CFF 解析失败 {exc}（改用位图或替代字体）")
        else:
            report.append(f"- {base}: {fext}/{ftype}，无 ToUnicode，需按字形名另处理")
        fonts.append(entry)
    report.append("")

    # ---- 逐字位置
    runs = []
    for sp in page.get_texttrace():
        chars = [{"ch": chr(c[0]), "x": round(c[2][0], 3), "y": round(c[2][1], 3),
                  "gid": c[1]} for c in sp["chars"]]
        runs.append({"font": sp["font"], "size": round(sp["size"], 3),
                     "color": sp["color"], "type": sp["type"], "chars": chars})
    with open(os.path.join(outdir, "trace.json"), "w", encoding="utf-8") as fh:
        json.dump(runs, fh, ensure_ascii=False, indent=1)

    report.append("## 文字行")
    for r in runs:
        txt = "".join(c["ch"] for c in r["chars"])
        hx = "#%02X%02X%02X" % tuple(int(round(v * 255)) for v in r["color"])
        report.append(f"- {hx} {r['size']:.2f}pt {r['font']}  y={r['chars'][0]['y']:.2f}  {txt!r}")
    report.append("")

    with open(os.path.join(outdir, "matrix.json"), "w", encoding="utf-8") as fh:
        json.dump({"page": [page.rect.width, H], "images": images, "fonts": fonts}, fh,
                  ensure_ascii=False, indent=1)
    with open(os.path.join(outdir, "report.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(report))

    doc.close()
    print("\n".join(report))
    print(f"\n产出: {outdir}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main(sys.argv))
