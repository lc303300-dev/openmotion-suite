# -*- coding: utf-8 -*-
"""Replace the whole animation block in gen_scene.py with the luxury-grade version."""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8")
P = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg\03-work\gen_scene.py"

src = io.open(P, encoding="utf-8").read()

START = '  <script>\n    (function () {{'
END = '      window.__timelines["scene-a"] = tl;'
i, j = src.index(START), src.index(END)

NEW = '''  <script>
    (function () {{
      const tl = gsap.timeline({{ paused: true }});

      /* 0 — 纯色底 → 纸纹极缓浮现；全程极轻推近 */
      tl.fromTo("#papered", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.62, ease: "power1.out" }}, 0.12);
      tl.fromTo("#bg-paper", {{ scale: 1.018 }}, {{ scale: 1.0, duration: 6.0, ease: "none" }}, 0.0);

      /* 1 — 相片自上而下依次落定：无弹跳、无压扁、无甩尾 */
      const drops = [
        ["#fall-note",    0.26, -640, 1.05],
        ["#fall-gate",    0.48, -700, 1.04],
        ["#fall-primary", 0.70, -740, 1.04],
        ["#fall-middle",  0.90, -780, 1.03]
      ];
      drops.forEach(function (d) {{
        const sel = d[0], t0 = d[1], fromY = d[2], fromScale = d[3];
        tl.fromTo(sel,
          {{ y: fromY, scaleX: fromScale, scaleY: fromScale }},
          {{ y: 0, scaleX: 1, scaleY: 1, duration: 0.84, ease: "power2.out" }}, t0);
        tl.fromTo(sel, {{ opacity: 0 }},
          {{ opacity: 1, duration: 0.68, ease: "power1.out" }}, t0 + 0.02);
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

'''

src = src[:i] + NEW + src[j:]
io.open(P, "w", encoding="utf-8").write(src)
print("animation block replaced;", len(src), "bytes")
