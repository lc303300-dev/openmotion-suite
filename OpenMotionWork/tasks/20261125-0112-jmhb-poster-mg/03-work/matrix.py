# -*- coding: utf-8 -*-
"""Exact-matrix layout: derive CSS matrices from PDF image transforms."""
import sys, os, json, math
sys.stdout.reconfigure(encoding="utf-8")
import fitz

BASE = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg"
SRC = r"F:\LiuCan\Work\20261123-JMHB\画板 16(1).pdf"
H = 1280.0

# name, content-stream cm (y-up), native pixel size
RAW = [
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


def femu(a, b, c, d, e, f, W, Hh):
    """unit-square y-down matrix -> pixel-basis matrix for a WxH element"""
    return (a / W, b / W, c / Hh, d / Hh, e, f)


def mmul(A, B):
    a1, b1, c1, d1, e1, f1 = A
    a2, b2, c2, d2, e2, f2 = B
    return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2,
            a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)


def minv(M):
    a, b, c, d, e, f = M
    det = a * d - b * c
    ia, ib, ic, id_ = d / det, -b / det, -c / det, a / det
    ie = -(ia * e + ic * f)
    if_ = -(ib * e + id_ * f)
    return (ia, ib, ic, id_, ie, if_)


mat = {}
for name, a, b, c, d, e, f, W, Hh in RAW:
    Md = (a, -b, -c, d, c + e, H - d - f)      # fitz y-down, unit basis
    mat[name] = {"unit": Md, "css": femu(*Md, W, Hh), "px": [W, Hh]}

def corners_css(name):
    a, b, c, d, e, f = mat[name]["unit"]
    pts = [(a * u + c * v + e, b * u + d * v + f) for u, v in [(0, 0), (1, 0), (0, 1), (1, 1)]]
    return pts

for n in mat:
    p = corners_css(n)
    xs = [q[0] for q in p]; ys = [q[1] for q in p]
    cx = sum(xs) / 4; cy = sum(ys) / 4
    a, b, c, d, e, f = mat[n]["unit"]
    det = a * d - b * c
    uw = math.hypot(a, b); vh = math.hypot(c, d)
    mat[n]["center"] = [round(cx, 3), round(cy, 3)]
    mat[n]["bbox"] = [round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2)]
    mat[n]["detSign"] = 1 if det > 0 else -1
    mat[n]["uw"] = round(uw, 3); mat[n]["vh"] = round(vh, 3)
    print(f"{n:8s} det={'+' if det>0 else '-'} uw={uw:7.2f} vh={vh:7.2f} "
          f"center=({cx:7.2f},{cy:7.2f}) bbox={mat[n]['bbox']}")

# nested photo matrices inside their frame sheet
pairs = [("frame1", "gate"), ("frame2", "primary"), ("frame3", "middle")]
for fr, ph in pairs:
    M1 = mat[fr]["css"]
    Mg = mat[ph]["css"]
    M2 = mmul(minv(M1), Mg)
    mat[ph]["inline"] = {
        "frame": fr,
        "matrix": [round(v, 7) for v in M2],
        "px": mat[ph]["px"],
    }
    # sanity: where does the photo land in sheet pixels
    a, b, c, d, e, f = M2
    W, Hh = mat[ph]["px"]
    pts = [(a * u + c * v + e, b * u + d * v + f) for u, v in [(0, 0), (W, 0), (0, Hh), (W, Hh)]]
    print(f"  {ph} in {fr}: corners {[(round(x,1), round(y,1)) for x, y in pts]}")

json.dump({k: {kk: vv for kk, vv in v.items() if kk != "unit"} for k, v in mat.items()},
          open(os.path.join(BASE, "03-work", "matrix.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\nwritten matrix.json")
