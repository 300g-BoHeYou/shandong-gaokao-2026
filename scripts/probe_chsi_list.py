# -*- coding: utf-8 -*-
"""测试 Python 直连 gaokao.chsi.com.cn 强基栏目与简章正文。"""
import re
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
      "Accept-Language": "zh-CN,zh;q=0.9"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        raw = r.read()
        enc = "utf-8"
        m = re.search(rb'charset=["\']?([\w-]+)', raw[:2000], re.I)
        if m:
            enc = m.group(1).decode("ascii", "ignore")
        return r.status, raw.decode(enc, errors="replace")


for url in ["https://gaokao.chsi.com.cn/gkxx/qjjh",
            "https://gaokao.chsi.com.cn/gkxx/qjjh/202604/20260407/2293461571.html"]:
    try:
        status, html = get(url)
        print(f"=== {url} -> HTTP {status}, {len(html)} chars")
        title = re.search(r"<title>(.*?)</title>", html, re.S)
        print("   title:", title.group(1).strip() if title else "-")
        links = re.findall(r"""href=["'](/gkxx/qjjh/[^"']+)["']""", html)
        print("   简章链接数:", len(set(links)))
        for l in sorted(set(links))[:8]:
            print("     ", l)
        # 正文片段
        body = re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.S | re.I)
        body = re.sub(r"<[^>]+>", " ", body)
        body = re.sub(r"\s+", " ", body)
        print("   正文前 300 字:", body[:300])
    except Exception as e:
        print(f"=== {url} FAILED: {type(e).__name__} {e}")
