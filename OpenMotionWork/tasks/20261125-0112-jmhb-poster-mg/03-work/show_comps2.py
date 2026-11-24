# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
P = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg\03-work\ae-export\manifest.json"
d = json.load(open(P, encoding="utf-8"))
comps = d.get("comps", [])
print("n comps:", len(comps))
for c in comps:
    print("\ncomp keys:", list(c.keys()))
    for k, v in c.items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            print("   ", k, "=", str(v)[:80])
    layers = c.get("layers") or c.get("items") or []
    print("   layers:", len(layers))
    for l in layers[:6]:
        print("      ", {k: str(v)[:28] for k, v in list(l.items())[:6]})
