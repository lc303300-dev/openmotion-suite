# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
P = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg\03-work\ae-export\manifest.json"
d = json.load(open(P, encoding="utf-8"))
print("root:", d.get("root"))
print("canvas:", d.get("width"), "x", d.get("height"), "@", d.get("fps"), "dur", d.get("duration"))
for c in d.get("comps", []):
    print("comp:", {k: v for k, v in c.items() if k in ("id", "name", "compName", "width", "height", "duration")})
    for l in c.get("layers", [])[:20]:
        print("   layer:", {k: v for k, v in l.items() if k in ("id", "name", "kind", "type", "parent", "parentId")})
