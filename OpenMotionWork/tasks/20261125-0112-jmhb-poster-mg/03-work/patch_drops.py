# -*- coding: utf-8 -*-
import io, sys
sys.stdout.reconfigure(encoding="utf-8")
p = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg\03-work\gen_scene.py"
s = io.open(p, encoding="utf-8").read()
pairs = [
    ('["#fall-note",    0.24, 760, 0.46]', '["#fall-note",    0.22, 860, 0.48]'),
    ('["#fall-gate",    0.50, 820, 0.48]', '["#fall-gate",    0.50, 940, 0.50]'),
    ('["#fall-primary", 0.78, 860, 0.50]', '["#fall-primary", 0.80, 1000, 0.52]'),
    ('["#fall-middle",  1.06, 900, 0.54]', '["#fall-middle",  1.10, 1060, 0.56]'),
]
for a, b in pairs:
    if a not in s:
        print("NOT FOUND:", a)
    s = s.replace(a, b)
io.open(p, "w", encoding="utf-8").write(s)
print("patched drops")
