# -*- coding: utf-8 -*-
"""在 chsi 强基页面 JS 中查找简章数据接口。"""
import re
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", errors="replace")


for js in ["https://t1.chei.com.cn/bm/jcxkzs/stu/assets/js/app-1.0.3.js"]:
    try:
        src = get(js)
    except Exception as e:
        print("FAIL", js, e)
        continue
    print("=== ", js, len(src))
    for m in re.finditer(r"""["']((?:/|https?://)[^"']{3,120})["']""", src):
        u = m.group(1)
        if any(k in u.lower() for k in ("jcxkzs", "api", "sch", "zszc", "jz", "notice", "ggtz", "detail")):
            print("   ", u)
    print("--- 含 'sch/' 或 axios/fetch 调用上下文 ---")
    for m in re.finditer(r"jcxkzs/[a-zA-Z0-9_/\.\-{}$+]*", src):
        print("   ctx:", m.group(0))
