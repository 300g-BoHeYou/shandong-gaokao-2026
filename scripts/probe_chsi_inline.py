# -*- coding: utf-8 -*-
"""打印 chsi 强基页面尾部的内联 Vue 脚本, 定位数据接口。"""
import re
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36",
      "Accept-Language": "zh-CN,zh;q=0.9"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


for url in ["https://bm.chsi.com.cn/jcxkzs/sch/10001", "https://bm.chsi.com.cn/jcxkzs/sch/ggtzs/10001"]:
    body = get(url)
    print("=" * 72)
    print(url, len(body))
    # 内联 script
    for m in re.finditer(r"<script(?![^>]*src)[^>]*>(.*?)</script>", body, re.S | re.I):
        code = m.group(1).strip()
        if len(code) < 40:
            continue
        print("-" * 60)
        print(code[:3000])
