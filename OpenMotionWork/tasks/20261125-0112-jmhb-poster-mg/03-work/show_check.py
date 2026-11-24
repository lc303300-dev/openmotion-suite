# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
p = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg\03-work\check.json"
d = json.load(open(p, encoding="utf-8-sig"))
print("ok =", d.get("ok"))
print("summary =", json.dumps(d.get("summary"), ensure_ascii=False))
for arr in ("errors", "warnings", "findings", "infos"):
    for f in d.get(arr, []):
        print("%-8s %-36s %-28s %s" % (f.get("severity"), f.get("code"),
                                       str(f.get("selector"))[:28], f.get("message")[:100]))
