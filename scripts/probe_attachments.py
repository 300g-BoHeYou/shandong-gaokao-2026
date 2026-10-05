# -*- coding: utf-8 -*-
"""列出各校 chsi 页的附件(existFjvo)并定位附件下载接口。"""
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "qj_cache"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"}

idx = json.loads((CACHE / "chsi_index.json").read_text(encoding="utf-8"))
print("=== 各校附件 ===")
for name, info in idx.items():
    p = CACHE / f"chsi_{info['code']}.html"
    if not p.exists():
        continue
    html = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"existFjvo:\s*(\[.*?\])", html, re.S)
    if m and m.group(1).strip() not in ("[]", "[ ]"):
        raw = m.group(1)
        names = re.findall(r'"filename":"((?:[^"\\]|\\.)*)"', raw)
        ids = re.findall(r'"fileid":"([^"]+)"', raw)
        print(f"  [{name}]")
        for i, (fn, fid) in enumerate(zip(names, ids)):
            fn = re.sub(r"\\u([0-9a-fA-F]{4})", lambda x: chr(int(x.group(1), 16)), fn)
            print(f"      {fn}  fileid={fid}")

print("\n=== 在 JS 中查找附件下载接口 ===")
for js in ["https://t1.chei.com.cn/bm/jcxkzs/stu/assets/js/app-1.0.3.js",
           "https://t4.chei.com.cn/common/js/api-1.0.4.js"]:
    try:
        src = urllib.request.urlopen(urllib.request.Request(js, headers=UA), timeout=40).read().decode("utf-8", "replace")
    except Exception as e:
        print("  FAIL", js, e)
        continue
    print(f"  --- {js} ({len(src)}B)")
    for kw in ["fileid", "Fj", "fj", "download", "downloadFj", "wj"]:
        cnt = src.count(kw)
        if cnt:
            print(f"     '{kw}' x{cnt}")
    for m in re.finditer(r"[\"']([^\"']*(?:[Ff]j|fileid|download)[^\"']*)[\"']", src):
        print("     路径:", m.group(1)[:100])
