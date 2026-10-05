# -*- coding: utf-8 -*-
"""探测软科专业排名页 URL 格式。"""
import requests

BASE = "https://www.shanghairanking.cn/rankings/bcmr/2026"
candidates = [
    BASE + "/080901",
    BASE + "/计算机科学与技术",
    BASE + "?majorCode=080901",
    BASE + "?major=080901",
    BASE + "?code=080901",
    BASE + "/080901 计算机科学与技术",
]
h = {"User-Agent": "Mozilla/5.0"}
for u in candidates:
    try:
        r = requests.get(u, headers=h, timeout=20, allow_redirects=False)
        loc = r.headers.get("Location", "")
        print(f"{r.status_code}  {u}  -> {loc}")
    except Exception as e:
        print("ERR", u, e)

# 看 state.js 里的路由/专业结构
r = requests.get("https://www.shanghairanking.cn/_nuxt/static/1786433071/rankings/bcmr/2026/state.js", headers=h, timeout=30)
print("\nstate.js status:", r.status_code, "len:", len(r.content))
t = r.content.decode("utf-8", errors="ignore")
# 找专业链接或路由
import re
# 找 majorCode / code 字段样例
for pat in [r"majorCode.{0,50}", r"majorCode[^,]{0,60}", r"080901.{0,60}", r"/rankings/bcmr/2026/[^\"']{0,60}"]:
    ms = re.findall(pat, t)[:5]
    if ms:
        print(f"\npattern {pat}:")
        for x in ms:
            print("  ", x[:80])
