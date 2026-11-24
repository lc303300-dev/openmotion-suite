# -*- coding: utf-8 -*-
"""Package the generated source together with the imported assets into a ZIP."""
import sys, os, shutil, json, zipfile
sys.stdout.reconfigure(encoding="utf-8")

BASE = r"F:\LiuCan\AI\DSH\OpenMotionWork\tasks\20261125-0112-jmhb-poster-mg"
SRC_PROJECT = r"F:\LiuCan\AI\DSH\OpenMotionWork\data\projects\d8db7db0-bd0a-4ce6-93c3-3d9f9545d06f"
BUILD = os.path.join(BASE, "03-work", "build")
PKG = os.path.join(BASE, "03-work", "pkg")
ZIP = os.path.join(BASE, "03-work", "jmhb-poster-6s.zip")

shutil.rmtree(PKG, ignore_errors=True)
os.makedirs(PKG, exist_ok=True)

# 1. copy everything the project owns (assets + metadata)
for name in os.listdir(SRC_PROJECT):
    src = os.path.join(SRC_PROJECT, name)
    dst = os.path.join(PKG, name)
    if os.path.isdir(src):
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)

# 2. overwrite the authored source
shutil.copy2(os.path.join(BUILD, "index.html"), os.path.join(PKG, "index.html"))
os.makedirs(os.path.join(PKG, "compositions"), exist_ok=True)
shutil.copy2(os.path.join(BUILD, "compositions", "scene-a.html"),
             os.path.join(PKG, "compositions", "scene-a.html"))

# 3. drop caches / state
for junk in (".hyperframes", "node_modules", ".git"):
    p = os.path.join(PKG, junk)
    if os.path.isdir(p):
        shutil.rmtree(p, ignore_errors=True)

# 4. verify referenced assets exist
import re
html = open(os.path.join(PKG, "compositions", "scene-a.html"), encoding="utf-8").read() + \
       open(os.path.join(PKG, "index.html"), encoding="utf-8").read()
refs = sorted(set(re.findall(r'assets/[A-Za-z0-9_\-./]+', html)))
missing = [r for r in refs if not os.path.exists(os.path.join(PKG, r.replace("/", os.sep)))]
print("asset refs:", len(refs), "missing:", missing or "none")
for r in refs:
    print("  ", r, os.path.getsize(os.path.join(PKG, r.replace("/", os.sep))))

# 5. zip
if os.path.exists(ZIP):
    os.remove(ZIP)
with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for root, dirs, files in os.walk(PKG):
        dirs[:] = [d for d in dirs if d not in (".hyperframes", "node_modules")]
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, PKG).replace(os.sep, "/")
            z.write(full, rel)
print("\nzip:", ZIP, os.path.getsize(ZIP), "bytes")
with zipfile.ZipFile(ZIP) as z:
    names = z.namelist()
print("entries:", len(names))
for n in names:
    print("  ", n)
