# -*- coding: utf-8 -*-
"""Summarize the hf2ae manifest: what became a real layer, what got flattened."""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8")
P = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg\03-work\ae-export\manifest.json"
d = json.load(open(P, encoding="utf-8"))
print("top keys:", list(d.keys()))

def walk(node, depth=0, path=""):
    if isinstance(node, dict):
        kind = node.get("kind") or node.get("type")
        name = node.get("name") or node.get("id") or ""
        if kind:
            keys = node.get("transformKeys") or node.get("keys") or []
            print(f"{'  '*depth}{kind:10s} {str(name)[:26]:26s} keys={len(keys) if hasattr(keys,'__len__') else keys}")
        for k, v in node.items():
            if k in ("children", "layers", "clips", "comps"):
                walk(v, depth + 1, k)
    elif isinstance(node, list):
        for it in node:
            walk(it, depth, path)

walk(d)
