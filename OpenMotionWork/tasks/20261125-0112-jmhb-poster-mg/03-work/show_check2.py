# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
p = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg\03-work\check.json"
d = json.load(open(p, encoding="utf-8-sig"))

def walk(node, path=""):
    if isinstance(node, dict):
        if "code" in node and "message" in node:
            print("%-46s %-8s %-26s %s" % (path, node.get("severity"), str(node.get("selector"))[:26],
                                           node.get("message", "")[:110]))
            return
        for k, v in node.items():
            walk(v, path + "/" + k if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, path)

for key in ("lint", "runtime", "layout", "motion", "contrast", "craft", "audio"):
    walk(d.get(key), key)
print("\n--- runtime summary ---")
print(json.dumps({k: v for k, v in d.get("runtime", {}).items() if not isinstance(v, (list, dict))}, ensure_ascii=False)[:600])
