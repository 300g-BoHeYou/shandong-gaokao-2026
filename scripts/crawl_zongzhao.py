# -*- coding: utf-8 -*-
"""抓取山东省2026年本科综合评价招生(综招)10所高校官方简章, 缓存到 zz_cache/。"""
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "zz_cache"
CACHE.mkdir(exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
      "Accept-Language": "zh-CN,zh;q=0.9"}

SCHOOLS = [
    ("山东大学", "http://www.bkzs.sdu.edu.cn/info/1028/2591.htm"),
    ("中国海洋大学", "http://bkzs.ouc.edu.cn/2024/0422/c17839a524977/page.htm"),
    ("中国石油大学（华东）", "https://zhaosheng.upc.edu.cn/cms/frontViewArticle.html?id=5b66a8ff3f0e4f04a74e1f74ca521c10"),
    ("哈尔滨工业大学（威海）", "http://zsb.hitwh.edu.cn/home/article/details?id=1576"),
    ("青岛大学", "https://zs.qdu.edu.cn/info/1004/2650.htm"),
    ("山东师范大学", "http://www.zsb.sdnu.edu.cn/info/1003/4642.htm"),
    ("山东科技大学", "https://zs.sdust.edu.cn/"),
    ("青岛科技大学", "https://zs.qust.edu.cn/info/1065/4874.htm"),
    ("山东财经大学", "https://zhaosheng.sdufe.edu.cn/f/newsCenter/article/8764805a5a7a4e599d9ea2ec62851923"),
    ("华南理工大学", "https://admission.scut.edu.cn/2026/0416/c30825a624737/page.htm"),
]


def fetch(name, url, idx):
    p = CACHE / f"zz_{idx:02d}.html"
    if p.exists() and p.stat().st_size > 2000:
        return p.read_text(encoding="utf-8", errors="replace"), "cache"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        raw = r.read()
    enc = "utf-8"
    m = re.search(rb'charset=["\']?([\w-]+)', raw[:3000], re.I)
    if m:
        enc = m.group(1).decode("ascii", "ignore")
    try:
        text = raw.decode(enc, errors="replace")
    except LookupError:
        text = raw.decode("utf-8", errors="replace")
    p.write_text(text, encoding="utf-8")
    return text, f"HTTP {len(raw)}B"


result = {}
for i, (name, url) in enumerate(SCHOOLS, 1):
    try:
        html, note = fetch(name, url, i)
        plain = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
        hits = [k for k in ["招生计划", "报名", "考核", "专业", "综合成绩", "面试", "笔试"] if k in plain]
        result[name] = {"url": url, "len": len(html), "note": note, "hits": len(hits), "file": f"zz_{i:02d}.html"}
        print(f"[{name}] {note} 命中{hits}")
    except urllib.error.HTTPError as e:
        result[name] = {"url": url, "error": f"HTTP {e.code}"}
        print(f"[{name}] HTTP {e.code} {url}")
    except Exception as e:
        result[name] = {"url": url, "error": f"{type(e).__name__}: {e}"}
        print(f"[{name}] {type(e).__name__} {url}")
    time.sleep(0.4)

(CACHE / "index.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
ok = sum(1 for v in result.values() if v.get("hits", 0) >= 4)
print(f"\n抓取完成: {ok}/{len(result)} 校可用")
