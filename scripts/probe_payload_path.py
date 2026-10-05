# -*- coding: utf-8 -*-
"""探测专业详情页的静态 payload/state 是否存在(确认路由真实性)。"""
import requests

h = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36",
    "Referer": "https://www.shanghairanking.cn/rankings/bcmr/2026",
}
base = "https://www.shanghairanking.cn/_nuxt/static/1786433071/rankings/bcmr/2026"
for path in ["/080901/state.js", "/080901/payload.js", "/100504K/state.js", "/100504K/payload.js"]:
    u = base + path
    r = requests.get(u, headers=h, timeout=30)
    txt = r.content.decode("utf-8", errors="ignore")
    print(f"{path}: status={r.status_code} len={len(r.content)}")
    if r.status_code == 200 and len(r.content) > 1000:
        for probe in ["计算机科学与技术", "蒙医学", "majorCode", "080901"]:
            if probe in txt:
                print(f"   含 {probe}: True")
