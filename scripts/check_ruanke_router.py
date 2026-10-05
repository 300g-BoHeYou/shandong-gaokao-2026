# -*- coding: utf-8 -*-
"""检查软科页面 JS/payload 中的路由定义, 确认专业链接格式。"""
import re
import requests

h = {"User-Agent": "Mozilla/5.0"}

# 1) payload.js (Nuxt 静态数据)
for u in [
    "https://www.shanghairanking.cn/_nuxt/static/1786433071/rankings/bcmr/2026/payload.js",
    "https://www.shanghairanking.cn/rankings/bcmr/2026/payload.js",
]:
    r = requests.get(u, headers=h, timeout=30)
    print("payload", u, "->", r.status_code, len(r.content))
    if r.status_code == 200:
        t = r.content.decode("utf-8", errors="ignore")
        ms = re.findall(r'"code":"[^"]{1,12}"[^}]{0,80}', t)[:8]
        for x in ms:
            print("  ", x[:110])
        # 找专业路由
        ms2 = re.findall(r"/rankings/bcmr/2026/[^\"']{1,40}", t)[:10]
        print("  routes:", ms2)

# 2) 主页面 JS bundle 找路由模式
r = requests.get("https://www.shanghairanking.cn/rankings/bcmr/2026", headers=h, timeout=30)
t = r.content.decode("utf-8", errors="ignore")
scripts = re.findall(r'src="([^"]*\.js[^"]*)"', t)
print("\n页面 JS:", scripts[:10])
for s in scripts[:6]:
    u = s if s.startswith("http") else "https://www.shanghairanking.cn" + s
    try:
        rr = requests.get(u, headers=h, timeout=60)
        print("js", u, rr.status_code, len(rr.content))
        body = rr.content.decode("utf-8", errors="ignore")
        # 搜索专业路由模式
        m = re.findall(r"[^\"]*bcmr/2026[^\"]*", body)[:10]
        for x in m:
            print("   route:", x[:120])
        m2 = re.findall(r"majorCode[^;]{0,60}", body)[:5]
        for x in m2:
            print("   majorCode:", x[:100])
        if m or m2:
            break
    except Exception as e:
        print("err", u, e)
