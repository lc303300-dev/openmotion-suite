# -*- coding: utf-8 -*-
"""Derive exact layout parameters from PDF images and write assets at 1.5x."""
import sys, os, json, math
sys.stdout.reconfigure(encoding="utf-8")
import fitz
from PIL import Image

SRC = r"F:\LiuCan\Work\20261123-JMHB\画板 16(1).pdf"
BASE = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg"
WEB = os.path.join(BASE, "02-assets", "web")
PROJ_ASSETS = os.path.join(BASE, "02-assets", "project")
os.makedirs(PROJ_ASSETS, exist_ok=True)

doc = fitz.open(SRC)
page = doc[0]

def corners(M):
    a, b, c, d, e, f = M
    pts = [(0, 0), (1, 0), (0, 1), (1, 1)]
    return [(a * u + c * v + e, b * u + d * v + f) for u, v in pts]

def describe(xref, W, H):
    infos = [i for i in page.get_image_info() if i["width"] == W and i["height"] == H]
    return infos

# explicit matrices from content stream, converted to fitz y-down by the library
targets = {
    "note":    (69, 242, 324),
    "gate":    (70, 845, 472),
    "frame1":  (72, 497, 683),
    "primary": (73, 745, 418),
    "frame2":  (72, 497, 683),
    "middle":  (74, 741, 414),
    "frame3":  (72, 497, 683),
    "stamp":   (76, 333, 161),
    "paper":   (67, 1300, 2815),
}

# matrix per drawn instance, in draw order, read from content stream (y-up) then converted.
# fitz y-down conversion: (a, -b, -c, -d, e, H-f)
H = 1280.0
raw = [
    # (name, a, b, c, d, e, f, W, H)
    ("paper",   762.2769594, 0, 0, 1650.6228006, -12.9958496, -137.1589334, 1300, 2815),
    ("note",    149.25913, -89.3518524, 119.6405934, 199.8554467, 378.3356029, 805.6572486, 242, 324),
    ("gate",    605.0280693, -62.0951977, 34.6577813, 337.6900517, -28.9969674, 617.9185803, 845, 472),
    ("frame1",  -55.5021268, -353.2631424, 485.2867533, -76.2447131, 63.6868795, 984.1231311, 497, 683),
    ("primary", 531.3544981, 68.1934443, -38.2967278, 298.4031636, 188.548908, 517.3721204, 745, 418),
    ("frame2",  50.5494611, -354.0057881, 486.3069124, 69.4411029, 166.2467986, 838.1985456, 497, 683),
    ("middle",  533.2216293, 0, 0, 297.7610797, 65.2138977, 477.1277143, 741, 414),
    ("frame3",  0, -357.5966843, 491.2398525, 0, 93.7083897, 801.5249023, 497, 683),
    ("stamp",   239.7191219, 0, 0, 115.4647155, 71.7538071, 481.3909364, 333, 161),
]

out = {}
for name, a, b, c, d, e, f, W, Hh in raw:
    # PDF image unit square has origin bottom-left; raster pixels top-left.
    # fitz transform (y-down, top-left origin):  (a, -b, -c, d, c+e, H-d-f)
    M = (a, -b, -c, d, c + e, H - d - f)
    pts = corners(M)
    cx = sum(p[0] for p in pts) / 4
    cy = sum(p[1] for p in pts) / 4
    # u vector -> local width direction; v vector -> local height direction
    ux, uy = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
    vx, vy = pts[2][0] - pts[0][0], pts[2][1] - pts[0][1]
    uw = math.hypot(ux, uy)
    vh = math.hypot(vx, vy)
    uang = math.degrees(math.atan2(uy, ux))
    vang = math.degrees(math.atan2(vy, vx))
    # visual bounding box
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    out[name] = {
        "center": [round(cx, 3), round(cy, 3)],
        "visualW": round(uw, 3), "visualH": round(vh, 3),
        "uAngleDeg": round(uang, 3), "vAngleDeg": round(vang, 3),
        "scaleX": round(uw / W, 5), "scaleY": round(vh / Hh, 5),
        "bbox": [round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2)],
        "px": [W, Hh],
    }
    print(f"{name:8s} center=({cx:7.2f},{cy:7.2f}) visual={uw:7.2f}x{vh:7.2f} "
          f"u={uang:7.2f} v={vang:7.2f} scale=({uw/W:.4f},{vh/Hh:.4f}) bbox={out[name]['bbox']}")

# --- card geometry: card content is a 3:4 sheet rotated; visual box = 491.24 x 357.6
for nm in ("frame1", "frame2", "frame3"):
    c = out[nm]
    ang = c["vAngleDeg"]
    # card rotation = vAngle normalized to (-90, 90]
    rot = ang
    while rot > 90: rot -= 180
    while rot <= -90: rot += 180
    out[nm]["cardRot"] = round(rot, 3)
    print(nm, "cardRot", round(rot, 3), "center", c["center"])

json.dump(out, open(os.path.join(BASE, "03-work", "layout.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# --- export 1.5x assets
SCALE = 1.5
mapping = {
    "paper.jpg":  ("paper.jpg", "RGB", 1.5),
    "gate.jpg":   ("gate.jpg", "RGB", 1.5),
    "primary.jpg": ("primary.jpg", "RGB", 1.5),
    "middle.jpg": ("middle.jpg", "RGB", 1.5),
    "note.png":   ("note.png", "RGBA", 1.5),
    "stamp.png":  ("stamp.png", "RGBA", 1.5),
}
for src_name, (dst_name, mode, k) in mapping.items():
    im = Image.open(os.path.join(WEB, src_name)).convert(mode)
    nw, nh = round(im.width * k), round(im.height * k)
    if (nw, nh) != im.size:
        im = im.resize((nw, nh), Image.LANCZOS)
    dst = os.path.join(PROJ_ASSETS, dst_name)
    if dst_name.endswith(".jpg"):
        im.save(dst, quality=94, subsampling=0)
    else:
        im.save(dst)
    print("asset", dst_name, im.size, os.path.getsize(dst), "bytes")

doc.close()
