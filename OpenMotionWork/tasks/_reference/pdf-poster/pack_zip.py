# -*- coding: utf-8 -*-
"""pack_zip.py — 把「已导入素材的 OpenMotion 工程」+「新写的源码」打成一个可导入的 ZIP。

为什么不用 openmotion_edit_project 直接传源码：几十 KB 的 HTML 通过对话搬运又慢又容易抄错。
打包导入是等价的（工程、素材、字体都进新工程），只是 projectId 会变。

用法:
    python pack_zip.py <project_dir> <build_dir> <out.zip>

    project_dir  已有工程的目录（含 assets/、hyperframes.json 等）
    build_dir    你生成的新源码目录（含 index.html、compositions/…）
    out.zip      输出

导入之后记得补一次元数据（requirements / assetNames），不传 files 就不会动源码：
    openmotion_edit_project(projectId, requestId, expectedRevision, expectedVersionId,
                            requirements=..., namingLanguage="zh-CN", assetNames=[...])

旧的空壳工程用 openmotion_manage_project(action="trash") 回收。
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import zipfile

JUNK_DIRS = {".hyperframes", "node_modules", ".git", ".DS_Store", ".thumbnails"}
REF_RE = re.compile(r"assets/[A-Za-z0-9_\-./]+")


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 2
    project_dir, build_dir, out_zip = argv[1], argv[2], argv[3]
    pkg = out_zip + ".pkg"
    shutil.rmtree(pkg, ignore_errors=True)
    os.makedirs(pkg, exist_ok=True)

    # 1. 工程自带的素材与元数据
    for name in os.listdir(project_dir):
        if name in JUNK_DIRS:
            continue
        src = os.path.join(project_dir, name)
        dst = os.path.join(pkg, name)
        if os.path.isdir(src):
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*JUNK_DIRS))
        else:
            shutil.copy2(src, dst)

    # 2. 用新源码覆盖
    for root, dirs, files in os.walk(build_dir):
        dirs[:] = [d for d in dirs if d not in JUNK_DIRS]
        for f in files:
            src = os.path.join(root, f)
            rel = os.path.relpath(src, build_dir)
            dst = os.path.join(pkg, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)

    # 3. 校验引用到的素材都在包里
    refs = set()
    for root, _dirs, files in os.walk(pkg):
        for f in files:
            if f.endswith((".html", ".css", ".js")):
                try:
                    text = open(os.path.join(root, f), encoding="utf-8", errors="ignore").read()
                except Exception:
                    continue
                refs.update(REF_RE.findall(text))
    missing = [r for r in sorted(refs)
               if not os.path.exists(os.path.join(pkg, r.replace("/", os.sep)))]
    if missing:
        print("!! 缺失素材:")
        for m in missing:
            print("   ", m)
        return 1
    print(f"素材引用 {len(refs)} 项，全部存在")

    # 4. 打包
    if os.path.exists(out_zip):
        os.remove(out_zip)
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for root, dirs, files in os.walk(pkg):
            dirs[:] = [d for d in dirs if d not in JUNK_DIRS]
            for f in files:
                full = os.path.join(root, f)
                z.write(full, os.path.relpath(full, pkg).replace(os.sep, "/"))

    size = os.path.getsize(out_zip)
    with zipfile.ZipFile(out_zip) as z:
        n = len(z.namelist())
    print(f"ZIP: {out_zip}  {n} 个文件  {size/1048576:.2f} MB")
    shutil.rmtree(pkg, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main(sys.argv))
