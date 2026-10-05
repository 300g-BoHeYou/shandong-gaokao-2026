# -*- coding: utf-8 -*-
"""检查软科专业排名页 URL 结构(专业链接格式)。"""
import re
import requests

url = "https://www.shanghairanking.cn/rankings/bcmr/2026"
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
print("status:", r.status_code, "len:", len(r.content))
t = r.content.decode("utf-8", errors="ignore")

links = re.findall(r'href="([^"]*bcmr[^"]*)"', t)
seen = []
for l in links:
    if l not in seen:
        seen.append(l)
print("含 bcmr 的链接:")
for l in seen[:40]:
    print("  ", l)

# 查找专业相关 JS/参数
m = re.findall(r"major[A-Za-z]*[=:][^,&\"'\s]{1,40}", t)
print("\nmajor 相关片段:")
for x in m[:20]:
    print("  ", x)

# 查找年份/专业链接模式
m2 = re.findall(r"/rankings/bcmr/2026/[^\"']{1,60}", t)
print("\n子路径链接:")
for x in m2[:20]:
    print("  ", x)
