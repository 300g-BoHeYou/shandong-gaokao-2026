# -*- coding: utf-8 -*-
"""补齐 中央民族大学 / 上海交通大学 / 四川大学 简章正文。"""
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "qj_cache"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36",
      "Accept-Language": "zh-CN,zh;q=0.9"}

CAND = {
    "中央民族大学": [
        "https://10052.gaokao.haedu.cn/policy/brochure/2026/0409/151490.html",
        "https://10052.gaokao.haedu.cn/brochure.html",
    ],
    "上海交通大学": [
        "https://gaokao.chsi.com.cn/gkxx/qjjh/202604/20260414/2293461887.html",
        "https://www.centv.cn/p/587802.html",
        "https://admissions.sjtu.edu.cn/newDetails?contentsID=3810000004182&name=%E9%87%8D%E8%A6%81%E8%B5%84%E8%AE%AF&xid=3810000004215",
    ],
    "四川大学": [
        "https://gaokao.chsi.com.cn/gkxx/qjjh/202604/20260411/2293468126.html",
        "https://10610.gaokao.haedu.cn/brochure.html",
    ],
}

for name, urls in CAND.items():
    print("=" * 70)
    print(name)
    for u in urls:
        try:
            req = urllib.request.Request(u, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                data = r.read()
            html = data.decode("utf-8", errors="replace")
            plain = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
            hits = [k for k in ["入围", "破格", "招生专业", "笔试", "综合成绩", "报名"] if k in plain]
            print(f"  OK {len(data):>7}B 命中{len(hits)}/6 {hits}  {u}")
            if len(hits) >= 3:
                fn = CACHE / f"fix_{abs(hash(name)) % 100000}_{abs(hash(u)) % 1000}.html"
                fn.write_text(html, encoding="utf-8")
                print("      -> 保存", fn.name)
                print("      片段:", plain[:150])
                break
        except urllib.error.HTTPError as e:
            print(f"  HTTP {e.code}  {u}")
        except Exception as e:
            print(f"  {type(e).__name__}  {u}")
