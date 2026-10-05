# -*- coding: utf-8 -*-
"""兰大: 用 IncompleteRead.partial 拿到正文。"""
import re
import urllib.request
from pathlib import Path

CACHE = Path(__file__).resolve().parent.parent / "qj_cache"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36",
      "Accept-Language": "zh-CN,zh;q=0.9"}

url = "https://zsb.lzu.edu.cn/zhaoshengdongtai/tongzhigonggao/2026/0409/330046.html"
try:
    data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
    print("完整读取", len(data))
except Exception as e:
    data = getattr(e, "partial", b"")
    print(f"{type(e).__name__}, 已获取部分 {len(data)}B")

if data:
    (CACHE / "lzu_jz.html").write_bytes(data)
    text = data.decode("utf-8", errors="replace")
    plain = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text))
    for kw in ["入围", "破格", "招生专业", "笔试", "倍"]:
        print(f"  '{kw}' x{plain.count(kw)}")
    print("  片段:", plain[:200])
