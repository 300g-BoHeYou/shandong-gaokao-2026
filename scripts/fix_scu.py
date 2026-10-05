# -*- coding: utf-8 -*-
"""从 haedu 四川大学简章列表页找强基简章链接并抓取。"""
import re
import urllib.parse
import urllib.request
from pathlib import Path

CACHE = Path(__file__).resolve().parent.parent / "qj_cache"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"}

base = "https://10610.gaokao.haedu.cn/brochure.html"
html = urllib.request.urlopen(urllib.request.Request(base, headers=UA), timeout=40).read().decode("utf-8", "replace")
links = re.findall(r'href="([^"]+)"[^>]*>([^<]{4,60})<', html)
cands = [(u, t.strip()) for u, t in links if "强基" in t or "强基" in u]
print("候选链接:")
for u, t in cands:
    print(f"  {t} -> {u}")

for u, t in cands[:4]:
    full = urllib.parse.urljoin(base, u)
    try:
        body = urllib.request.urlopen(urllib.request.Request(full, headers=UA), timeout=45).read().decode("utf-8", "replace")
        plain = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body))
        hits = [k for k in ["入围", "破格", "招生专业", "笔试", "综合成绩"] if k in plain]
        print(f"  {full} -> {len(body)}B 命中 {hits}")
        if len(hits) >= 3:
            (CACHE / "fix_scu_jz.html").write_text(body, encoding="utf-8")
            print("   -> 已保存 fix_scu_jz.html")
            break
    except Exception as e:
        print(f"  {full} -> {type(e).__name__} {e}")
