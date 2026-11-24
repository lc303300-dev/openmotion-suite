# -*- coding: utf-8 -*-
"""Generate index.html + compositions/scene-a.html using exact PDF matrices."""
import sys, os, json, html
sys.stdout.reconfigure(encoding="utf-8")

BASE = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg"
WORK = os.path.join(BASE, "03-work")
OUTDIR = os.path.join(WORK, "build")
os.makedirs(OUTDIR, exist_ok=True)

mat = json.load(open(os.path.join(WORK, "matrix.json"), encoding="utf-8"))
trace = json.load(open(os.path.join(WORK, "text-trace.json"), encoding="utf-8"))
glyphs = json.load(open(os.path.join(BASE, "02-assets", "web", "botera_glyphs.json"), encoding="utf-8"))

IMG = {
    "paper":   "assets/imported/bf234e55-6bd4-4967-85b7-df0a0f128c97.jpg",
    "gate":    "assets/imported/f545d046-5d0e-4dfc-a168-3483288dd5b7.jpg",
    "primary": "assets/imported/6708c943-01f0-4ad2-8403-fa437768bc2a.jpg",
    "middle":  "assets/imported/33b49ce4-1d7f-4faa-adc9-d7961e28064d.jpg",
    "note":    "assets/imported/f8361ab7-8393-4918-91cd-39fcb29491a1.png",
    "stamp":   "assets/imported/9a33f55d-04a8-4235-90ae-5702f7bd61e7.png",
}
F_MED = "HarmonyOS Sans SC Medium"
F_LIGHT = "HarmonyOS Sans SC Light"
F_AS = "AssassinDisplay"
FONT_FACES = f"""    @font-face {{ font-family: "{F_MED}"; src: url("assets/fonts/7ddbdc9d-0296-45c3-b630-c718ab8125b1.ttf"); font-weight: 500; font-style: normal; }}
    @font-face {{ font-family: "{F_LIGHT}"; src: url("assets/fonts/255ff3d9-2ccc-4b7f-9309-d2ffe867f2cc.ttf"); font-weight: 300; font-style: normal; }}
    @font-face {{ font-family: "{F_AS}"; src: url("assets/fonts/e8e685ae-6bcd-4b06-9727-fe23c723c2e9.ttf"); font-weight: 400; font-style: normal; }}
    @font-face {{ font-family: "SongPunct"; src: local("SimSun"), local("宋体"), local("Arial"); }}"""

# frame.png content box: paper mat (33,36)-(457,631); inner window (45,51)-(437,617)
MAT_BOX = dict(left=33, top=36, width=425, height=596)
WIN_BOX = dict(left=45, top=51, width=393, height=567)

def mx(m):
    return "matrix(" + ",".join(f"{v:.7f}" for v in m) + ")"

def mx_shift(m, dx, dy):
    a, b, c, d, e, f = m
    return mx((a, b, c, d, e - dx, f - dy))


def shadow_for(m):
    """Return a box-shadow local to the sheet that projects downward on the page."""
    a, b, c, d, e, f = m
    det = a * d - b * c
    # inverse rotation part: page (0,1) -> local
    lx = (-c) / det
    ly = a / det
    n = (lx ** 2 + ly ** 2) ** 0.5
    lx, ly = lx / n, ly / n
    scale = (a ** 2 + b ** 2) ** 0.5
    dist = 9.0 / scale
    blur = 19.0 / scale
    return f"{lx * dist:.2f}px {ly * dist:.2f}px {blur:.1f}px rgba(89,87,87,0.30)"


def fall(name, center):
    cx, cy = center
    return f'<div class="fall" id="fall-{name}" style="transform-origin:{cx:.3f}px {cy:.3f}px">'

# ---------- text
r_cn1 = [r for r in trace if r["font"].startswith("HarmonyOS_Sans_SC_Light")][0]
r_cn2 = [r for r in trace if r["font"].startswith("HarmonyOS_Sans_SC_Medium") and abs(r["chars"][0]["y"] - 951.37) < 0.4][0]
r_cn3 = [r for r in trace if r["font"].startswith("HarmonyOS_Sans_SC_Medium") and abs(r["chars"][0]["y"] - 992.45) < 0.4 and len(r["chars"]) == 10][0]
r_hl = [r for r in trace if r["font"].startswith("HarmonyOS_Sans_SC_Medium") and abs(r["chars"][0]["y"] - 992.45) < 0.4 and len(r["chars"]) == 2][0]

EN = {}
for r in trace:
    if r["font"] in ("Assassin$", "AdobeSongStd-Light") and r["size"] < 12:
        for c in r["chars"]:
            EN.setdefault(round(c["y"], 2), []).append(c)
EN_LINES = {y: sorted(ch, key=lambda c: c["x"]) for y, ch in EN.items()}
EN_Y = sorted(EN_LINES)

HL = dict(x=470.377, y=964.37, w=69.065, h=32.62)


def e(s):
    return html.escape(s, quote=True)


def poly():
    out, n = [], 0
    for c in [r for r in trace if r["font"].startswith("BoteraTFE") and abs(r["size"] - 64.74) < 0.1][0]["chars"]:
        if not c["ch"].strip():
            continue
        out.append(f'<g transform="translate({c["x"]:.3f},221.697)"><g class="glyph" data-g="{n}">'
                   f'<g transform="scale(0.0647397,-0.0704741)"><path d="{glyphs[c["ch"]]["path"]}"/></g></g></g>')
        n += 1
    return "\n        ".join(out)


def centro():
    out = []
    for i, c in enumerate([r for r in trace if r["font"].startswith("BoteraTFE") and abs(r["size"] - 33.85) < 0.1][0]["chars"]):
        out.append(f'<g transform="translate({c["x"]:.3f},250.547)"><g class="glyph" data-c="{i}" data-x="{c["x"]:.3f}">'
                   f'<g transform="scale(0.0338515,-0.0288139)"><path d="{glyphs[c["ch"]]["path"]}"/></g></g></g>')
    return "\n        ".join(out)


def chars(chars_, extra=""):
    out = []
    for c in chars_:
        if c["ch"] == " ":
            continue
        out.append(f'<text {extra}x="{c["x"]:.3f}" y="{c["y"]:.3f}">{e(c["ch"])}</text>')
    return "\n          ".join(out)


def en_block(y, gid):
    parts = []
    for c in EN_LINES[y]:
        if c["ch"] == " ":
            continue
        punct = c["ch"] in "/-.,"
        fam = "SongPunct" if punct else F_AS
        parts.append(f'<text font-family="{fam}" x="{c["x"]:.3f}" y="{c["y"]:.3f}">{e(c["ch"])}</text>')
    return f'<g id="{gid}" data-layout-allow-overlap>\n          ' + "\n          ".join(parts) + "\n        </g>"


EN_HTML = "\n        ".join(en_block(y, f"en{chr(65 + i)}") for i, y in enumerate(EN_Y))

# ---------- photo cards
def card_html(cid, frame, photo, alt):
    m_sheet = mat[frame]["css"]
    m_photo = mat[photo]["inline"]["matrix"]
    pw, ph = mat[photo]["px"]
    c = mat[frame]["center"]
    return f"""{fall(cid, c)}
        <div class="sheet" style="width:497px;height:683px;transform:{mx(m_sheet)}">
          <div class="mat" style="left:{MAT_BOX['left']}px;top:{MAT_BOX['top']}px;width:{MAT_BOX['width']}px;height:{MAT_BOX['height']}px;box-shadow:{shadow_for(m_sheet)}"></div>
          <div class="win" style="left:{WIN_BOX['left']}px;top:{WIN_BOX['top']}px;width:{WIN_BOX['width']}px;height:{WIN_BOX['height']}px">
            <img src="{IMG[photo]}" width="{pw}" height="{ph}" style="width:{pw}px;height:{ph}px;transform:{mx_shift(m_photo, WIN_BOX['left'], WIN_BOX['top'])}" alt="{alt}">
          </div>
        </div>
      </div>"""


CARD_NOTE = f"""{fall('note', mat['note']['center'])}
        <div class="sheet note" style="width:242px;height:324px;transform:{mx(mat['note']['css'])}">
          <img src="{IMG['note']}" width="242" height="324" style="width:242px;height:324px" alt="手写便签">
        </div>
      </div>"""

CARD_STAMP = f"""{fall('stamp', mat['stamp']['center'])}
        <div class="sheet stamp" style="width:333px;height:161px;transform:{mx(mat['stamp']['css'])}">
          <img src="{IMG['stamp']}" width="333" height="161" style="width:333px;height:161px" alt="金色邮戳">
        </div>
      </div>"""

SCENE = f"""<template>
  <style>
{FONT_FACES}

    #root {{ position: absolute; inset: 0; background: #E7DFD9; overflow: hidden; }}
    #stage {{ position: absolute; left: 0; top: 0; width: 720px; height: 1280px;
              transform: scale(1.5); transform-origin: 0 0; overflow: hidden; background: #E7DFD9; }}
    .clip {{ position: absolute; inset: 0; }}
    .holder {{ position: absolute; inset: 0; }}

    #bg-paper {{ position: absolute; inset: 0; }}
    #bg-paper img {{ position: absolute; left: 0; top: 0; transform-origin: 0 0;
                     width: 1300px; height: 2815px; transform: {mx(mat['paper']['css'])}; }}

    .fall {{ position: absolute; inset: 0; }}
    .sheet {{ position: absolute; left: 0; top: 0; transform-origin: 0 0; }}
    .mat {{ position: absolute; background: #FCFBF9; }}
    .win {{ position: absolute; overflow: hidden; background: #EFE8E2; }}
    .win img {{ position: absolute; left: 0; top: 0; transform-origin: 0 0; }}
    .sheet.note {{ background: transparent; box-shadow: none; }}
    .sheet.note img {{ position: absolute; inset: 0; filter: drop-shadow(7px 12px 30px rgba(89,87,87,0.30)); }}
    .sheet.stamp {{ background: transparent; box-shadow: none; }}
    .sheet.stamp img {{ position: absolute; inset: 0; }}

    #type {{ position: absolute; left: 0; top: 0; width: 720px; height: 1280px; }}
  </style>

  <div id="root" data-composition-id="scene-a" data-width="1080" data-height="1920">
    <div id="stage">

      <div class="clip" data-start="0" data-duration="6" id="clip-bg">
        <div class="holder">
          <div id="bg-paper"><img id="papered" src="{IMG['paper']}" alt=""></div>
        </div>
      </div>

      <div class="clip" data-start="0" data-duration="6" id="clip-photos" data-layout-allow-overflow>
        <div class="holder" id="photos">
      {CARD_NOTE}
      {card_html('gate', 'frame1', 'gate', '汉江书院牌坊')}
      {card_html('primary', 'frame2', 'primary', '武汉小学正门')}
      {card_html('middle', 'frame3', 'middle', '武珞路中学正门')}
        </div>
      </div>

      <div class="clip" data-start="0" data-duration="6" id="clip-stamp">
        <div class="holder">
      {CARD_STAMP}
        </div>
      </div>

      <div class="clip" data-start="0" data-duration="6" id="clip-type">
        <div class="holder">
          <svg id="type" viewBox="0 0 720 1280" width="720" height="1280" xmlns="http://www.w3.org/2000/svg">
            <g id="logo" fill="#562C80">
        {poly()}
        {centro()}
            </g>

            <g id="l1" data-layout-allow-overlap fill="#351217" font-family="{F_LIGHT}" font-size="{r_cn1['size']:.3f}">
          {chars(r_cn1['chars'][:5], 'data-half="left" ')}
          {chars(r_cn1['chars'][5:], 'data-half="right" ')}
            </g>

            <g id="l2" data-layout-allow-overlap fill="#351217" font-family="{F_MED}" font-size="{r_cn2['size']:.3f}">
          {chars(r_cn2['chars'])}
            </g>

            <g id="l3" data-layout-allow-overlap fill="#351217" font-family="{F_MED}" font-size="{r_cn3['size']:.3f}">
          {chars(r_cn3['chars'])}
            </g>

            <g id="l3b" data-layout-allow-overlap fill="#351217" font-family="{F_MED}" font-size="{r_hl['size']:.3f}">
          {chars(r_hl['chars'])}
            </g>

            <g id="en" data-layout-allow-overlap fill="#5E4636" font-size="11.542">
        {EN_HTML}
            </g>

            <clipPath id="hlclip"><rect id="hlreveal" x="{HL['x']}" y="{HL['y'] - 1}" width="0" height="{HL['h'] + 2}"/></clipPath>
            <g clip-path="url(#hlclip)">
              <rect x="{HL['x']}" y="{HL['y']}" width="{HL['w']}" height="{HL['h']}" fill="#562C80"/>
              <g fill="#FFFFFF" font-family="{F_MED}" font-size="{r_hl['size']:.3f}">
          {chars(r_hl['chars'])}
              </g>
            </g>
          </svg>
        </div>
      </div>

    </div>
  </div>

  <script>
    (function () {{
      const tl = gsap.timeline({{ paused: true }});

      /* 0 — 纯色底 → 纸纹极缓浮现；全程极轻推近 */
      tl.fromTo("#papered", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.62, ease: "power1.out" }}, 0.12);
      tl.fromTo("#bg-paper", {{ scale: 1.018 }}, {{ scale: 1.0, duration: 6.0, ease: "none" }}, 0.0);

      /* 1 — 相片自上而下依次落定：无弹跳、无压扁、无甩尾 */
      const drops = [
        ["#fall-note",    0.26, -640, 1.05],
        ["#fall-gate",    0.48, -700, 1.04],
        ["#fall-primary", 0.70, -790, 1.04],
        ["#fall-middle",  0.90, -860, 1.03]
      ];
      drops.forEach(function (d) {{
        const sel = d[0], t0 = d[1], fromY = d[2], fromScale = d[3];
        tl.fromTo(sel,
          {{ y: fromY, scaleX: fromScale, scaleY: fromScale }},
          {{ y: 0, scaleX: 1, scaleY: 1, duration: 0.84, ease: "power2.out" }}, t0);
        tl.fromTo(sel, {{ opacity: 0 }},
          {{ opacity: 1, duration: 0.38, ease: "power2.out" }}, t0 + 0.03);
      }});

      /* 2 — 主标：逐字母轻抬；CENTRO 字距只做极克制的聚拢 */
      tl.fromTo(".glyph[data-g]", {{ y: 13, opacity: 0 }},
        {{ y: 0, opacity: 1, duration: 0.92, ease: "power3.out", stagger: 0.05 }}, 0.66);
      tl.fromTo(".glyph[data-c]",
        {{ x: function (i, el) {{ return (354.55 - parseFloat(el.dataset.x)) * 0.13; }}, opacity: 0 }},
        {{ x: 0, opacity: 1, duration: 0.95, ease: "power3.out", stagger: 0.05 }}, 1.70);

      /* 3 — 印章：沉稳压下，落定即止 */
      tl.fromTo("#fall-stamp",
        {{ scale: 1.075, rotation: -1.2, opacity: 0, y: -9 }},
        {{ scale: 1, rotation: 0, opacity: 1, y: 0, duration: 0.46, ease: "power2.out" }}, 1.82);

      /* 4 — 校名：两侧向中心缓缓靠拢 */
      tl.fromTo("#l1 text[data-half=left]", {{ x: -58, opacity: 0 }},
        {{ x: 0, opacity: 1, duration: 0.80, ease: "power3.out", stagger: 0.008 }}, 2.18);
      tl.fromTo("#l1 text[data-half=right]", {{ x: 58, opacity: 0 }},
        {{ x: 0, opacity: 1, duration: 0.80, ease: "power3.out", stagger: 0.008 }}, 2.22);

      /* 5 — 文案：逐字浮现，只动透明度 */
      tl.fromTo("#l2 text", {{ opacity: 0 }},
        {{ opacity: 1, duration: 0.26, ease: "power1.out", stagger: 0.05 }}, 2.92);
      tl.fromTo("#l3 text", {{ opacity: 0 }},
        {{ opacity: 1, duration: 0.26, ease: "power1.out", stagger: 0.042 }}, 3.30);
      tl.fromTo("#l3b text", {{ opacity: 0 }},
        {{ opacity: 1, duration: 0.24, ease: "power1.out", stagger: 0.06 }}, 3.86);

      /* 6 — 英文：整行淡入，极轻上浮 */
      tl.fromTo("#enA text", {{ opacity: 0, y: 3 }}, {{ opacity: 1, y: 0, duration: 0.80, ease: "power2.out" }}, 4.06);
      tl.fromTo("#enB text", {{ opacity: 0, y: 3 }}, {{ opacity: 1, y: 0, duration: 0.80, ease: "power2.out" }}, 4.14);
      tl.fromTo("#enC text", {{ opacity: 0, y: 3 }}, {{ opacity: 1, y: 0, duration: 0.80, ease: "power2.out" }}, 4.22);

      /* 7 — 归处标亮：缓慢扫入收束 */
      tl.fromTo("#hlreveal", {{ attr: {{ width: 0 }} }},
        {{ attr: {{ width: {HL['w']} }}, duration: 0.56, ease: "power2.inOut" }}, 4.92);

      window.__timelines["scene-a"] = tl;
    }})();
  </script>
</template>
"""

INDEX = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>保利 POLY RARE · 双本部名校为邻（6s 9:16）</title>
  <script src="assets/gsap.min.js"></script>
  <style>
    html, body { margin: 0; padding: 0; background: #000; }
    #main { position: relative; width: 1080px; height: 1920px; overflow: hidden; background: #000; }
  </style>
</head>
<body>
  <div id="main" data-composition-id="main" data-start="0" data-duration="6"
       data-width="1080" data-height="1920" data-fps="30">
    <div id="scene-a" data-composition-id="scene-a"
         data-composition-src="compositions/scene-a.html"
         data-start="0" data-duration="6" data-track-index="0" data-track-kind="graphics"
         data-width="1080" data-height="1920"></div>
  </div>
  <script>
    window.__timelines = { main: gsap.timeline({ paused: true }) };
  </script>
</body>
</html>
"""

open(os.path.join(OUTDIR, "index.html"), "w", encoding="utf-8").write(INDEX)
os.makedirs(os.path.join(OUTDIR, "compositions"), exist_ok=True)
open(os.path.join(OUTDIR, "compositions", "scene-a.html"), "w", encoding="utf-8").write(SCENE)
print("index.html", len(INDEX), "scene-a.html", len(SCENE))
