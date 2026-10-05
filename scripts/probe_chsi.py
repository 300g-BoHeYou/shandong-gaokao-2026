# -*- coding: utf-8 -*-
"""探查 chsi 强基报名平台页面的嵌套链接结构。"""
import re
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


html = get("https://bm.chsi.com.cn/jcxkzs/sch/10001")
print("LEN", len(html))
print("\n==== 链接 ====")
for m in re.finditer(r"""<a\b[^>]*href=["']([^"']+)["'][^>]*>(.*?)</a>""", html, re.S | re.I):
    text = re.sub(r"<[^>]+>", "", m.group(2)).strip()
    print("  ", text[:40], "->", m.group(1))

print("\n==== 脚本/资源 ====")
for m in re.finditer(r"""(?:src|href)=["']([^"']+\.(?:js|json|css)[^"']*)["']""", html):
    print("  ", m.group(1))

print("\n==== 关键片段 ====")
for kw in ["zszc", "jianzhang", "zdzc", "article", "detail", "简章"]:
    for m in re.finditer(kw, html):
        s = max(0, m.start() - 100)
        print(f"  [{kw}] ...{html[s:m.start() + 120]}...".replace("\n", " "))
        break
