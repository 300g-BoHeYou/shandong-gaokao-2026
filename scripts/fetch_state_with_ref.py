# -*- coding: utf-8 -*-
"""带 Referer 抓取软科 state.js, 确认专业路由与代码。"""
import re
import requests

h = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Referer": "https://www.shanghairanking.cn/rankings/bcmr/2026",
    "Accept": "*/*",
}
u = "https://www.shanghairanking.cn/_nuxt/static/1786433071/rankings/bcmr/2026/state.js"
r = requests.get(u, headers=h, timeout=30)
print("status:", r.status_code, "len:", len(r.content))
if r.status_code == 200:
    t = r.content.decode("utf-8", errors="ignore")
    # 找 080901 出现
    for probe in ["080901", "majorCode", "computerScience", "route", "path:"]:
        idx = t.find(probe)
        print(f"\n'{probe}' 首次出现 @{idx}")
        if idx >= 0:
            print("   ", t[idx - 80:idx + 150].replace("\n", " ")[:230])
