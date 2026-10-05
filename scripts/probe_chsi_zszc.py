# -*- coding: utf-8 -*-
"""查看 chsi 强基 zszc / ggtzs 接口返回内容。"""
import re
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36",
      "Accept-Language": "zh-CN,zh;q=0.9", "Referer": "https://bm.chsi.com.cn/jcxkzs/sch/10001",
      "X-Requested-With": "XMLHttpRequest"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read().decode("utf-8", errors="replace")


for url in ["https://bm.chsi.com.cn/jcxkzs/sch/zszc?yxdm=10001",
            "https://bm.chsi.com.cn/jcxkzs/sch/ggtzs/10001"]:
    st, body = get(url)
    print("=" * 70)
    print(url, "->", st, len(body))
    print(body[:2500])
