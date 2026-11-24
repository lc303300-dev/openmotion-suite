# -*- coding: utf-8 -*-
import io, sys
sys.stdout.reconfigure(encoding="utf-8")
p = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg\03-work\gen_scene.py"
s = io.open(p, encoding="utf-8").read()

pairs = [
    ('<g id="l1" fill="#351217"', '<g id="l1" data-layout-allow-overlap fill="#351217"'),
    ('<g id="l2" fill="#351217"', '<g id="l2" data-layout-allow-overlap fill="#351217"'),
    ('<g id="l3" fill="#351217"', '<g id="l3" data-layout-allow-overlap fill="#351217"'),
    ('<g id="l3b" fill="#351217"', '<g id="l3b" data-layout-allow-overlap fill="#351217"'),
    ('<g id="en" fill="#5E4636"', '<g id="en" data-layout-allow-overlap fill="#5E4636"'),
    ('<g id="{gid}">', '<g id="{gid}" data-layout-allow-overlap>'),
]
for a, b in pairs:
    if a not in s:
        print("NOT FOUND:", a)
    s = s.replace(a, b)
io.open(p, "w", encoding="utf-8").write(s)
print("patched overlap flags")
