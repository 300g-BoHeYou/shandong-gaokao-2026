# -*- coding: utf-8 -*-
"""探测 bm.chsi.com.cn 强基简章数据接口 + 检查工作区写入。"""
import re
import urllib.error
import urllib.request
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36",
      "Accept-Language": "zh-CN,zh;q=0.9", "Referer": "https://bm.chsi.com.cn/jcxkzs/sch/10001"}

ROOT = Path(__file__).resolve().parent.parent


def probe(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            data = r.read()
        text = data.decode("utf-8", errors="replace")
        title = re.search(r"<title>(.*?)</title>", text, re.S)
        label = title.group(1).strip()[:40] if title else repr(text[:60])
        return f"HTTP {r.status} {len(data):>7}B  {label}"
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}"
    except Exception as e:
        return f"FAIL {type(e).__name__}"


cands = [
    "https://bm.chsi.com.cn/jcxkzs/sch/zszc/10001",
    "https://bm.chsi.com.cn/jcxkzs/sch/10001/zszc",
    "https://bm.chsi.com.cn/jcxkzs/zszc/10001",
    "https://bm.chsi.com.cn/jcxkzs/sch/zszc?yxdm=10001",
    "https://bm.chsi.com.cn/jcxkzs/sch/10001/zszc.html",
    "https://bm.chsi.com.cn/jcxkzs/sch/detail/10001",
    "https://bm.chsi.com.cn/jcxkzs/stu/sch/zszc/10001",
    "https://bm.chsi.com.cn/jcxkzs/ggtzs/10001",
    "https://bm.chsi.com.cn/jcxkzs/sch/ggtzs/10001",
    "https://bm.chsi.com.cn/jcxkzs/api/sch/10001",
    "https://bm.chsi.com.cn/jcxkzs/sch/10001/jz",
    "https://bm.chsi.com.cn/jcxkzs/sch/zszc?schId=10001",
]
for u in cands:
    print(f"{probe(u):<52} {u}")

print("\n=== 写入测试 ===")
for p in [ROOT / "_tmp_write_test.txt", ROOT / "scripts" / "_tmp_write_test.txt"]:
    try:
        p.write_text("ok", encoding="utf-8")
        print("  OK  ", p)
        p.unlink()
    except Exception as e:
        print("  FAIL", p, type(e).__name__, e)
