# -*- coding: utf-8 -*-
"""打印 chsi 强基 JS 中的所有路径字符串, 定位接口。"""
import re
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"}
req = urllib.request.Request("https://t1.chei.com.cn/bm/jcxkzs/stu/assets/js/app-1.0.3.js", headers=UA)
src = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", errors="replace")

paths = set()
for m in re.finditer(r"""["'`]([^"'`\s]{2,140})["'`]""", src):
    v = m.group(1)
    if v.startswith("/") or "chsi" in v or v.startswith("api"):
        paths.add(v)
for p in sorted(paths):
    print(p)

print("\n=== 'this.$http' / axios 附近的调用 ===")
for m in re.finditer(r"(?:this\.\$http|axios|\$\.(?:get|post|ajax))[^\n]{0,160}", src):
    print("  ", m.group(0)[:170])
