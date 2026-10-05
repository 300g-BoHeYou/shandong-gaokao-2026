# -*- coding: utf-8 -*-
"""抓取 chsi 强基报名平台页 -> 提取内联简章信息与外链 -> 抓取各校官方简章。

缓存写到仓库根目录 qj_cache/ (scripts/ 下 Python 写入受沙箱限制)。
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "qj_cache"
CACHE.mkdir(exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
      "Accept-Language": "zh-CN,zh;q=0.9"}

SCHOOLS = [
    ("北京大学", "10001"), ("中国人民大学", "10002"), ("清华大学", "10003"), ("北京航空航天大学", "10006"),
    ("北京理工大学", "10007"), ("中国农业大学", "10019"), ("北京师范大学", "10027"), ("中央民族大学", "10052"),
    ("南开大学", "10055"), ("天津大学", "10056"), ("大连理工大学", "10141"), ("东北大学", "10145"),
    ("吉林大学", "10183"), ("哈尔滨工业大学", "10213"), ("复旦大学", "10246"), ("同济大学", "10247"),
    ("上海交通大学", "10248"), ("华东师范大学", "10269"), ("南京大学", "10284"), ("东南大学", "10286"),
    ("浙江大学", "10335"), ("中国科学技术大学", "10358"), ("厦门大学", "10384"), ("山东大学", "10422"),
    ("中国海洋大学", "10423"), ("武汉大学", "10486"), ("华中科技大学", "10487"), ("湖南大学", "10532"),
    ("中南大学", "10533"), ("中山大学", "10558"), ("华南理工大学", "10561"), ("四川大学", "10610"),
    ("重庆大学", "10611"), ("电子科技大学", "10614"), ("西安交通大学", "10698"), ("西北工业大学", "10699"),
    ("西北农林科技大学", "10712"), ("兰州大学", "10730"), ("国防科技大学", "92002"),
]


def fetch(url, cache_name=None, timeout=40):
    if cache_name:
        p = CACHE / cache_name
        if p.exists() and p.stat().st_size > 500:
            return p.read_text(encoding="utf-8", errors="replace")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    enc = "utf-8"
    m = re.search(rb'charset=["\']?([\w-]+)', raw[:3000], re.I)
    if m:
        enc = m.group(1).decode("ascii", "ignore")
    try:
        text = raw.decode(enc, errors="replace")
    except LookupError:
        text = raw.decode("utf-8", errors="replace")
    if cache_name:
        (CACHE / cache_name).write_text(text, encoding="utf-8")
    return text


def js_unescape(s):
    s = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)
    for a, b in [('\\"', '"'), ("\\'", "'"), ("\\/", "/"), ("\\n", "\n"), ("\\r", ""), ("\\t", " "), ("\\\\", "\\")]:
        s = s.replace(a, b)
    return s


def parse_chsi(html):
    """从报名平台页提取 标题/报名时间/外链。"""
    out = {}
    m = re.search(r'jzbt:\s*"((?:[^"\\]|\\.)*)"', html)
    if m:
        out["title"] = js_unescape(m.group(1)).strip()
    m = re.search(r'time:\s*"((?:[^"\\]|\\.)*)"', html)
    if m:
        out["time"] = js_unescape(m.group(1)).strip()
    m = re.search(r'content:\s*"((?:[^"\\]|\\.)*)"', html, re.S)
    content_html = js_unescape(m.group(1)) if m else ""
    out["content_html"] = content_html
    links = []
    for lm in re.finditer(r"""href=["']([^"']+)["'][^>]*>(.*?)</a>""", content_html, re.S | re.I):
        text = re.sub(r"<[^>]+>", "", lm.group(2)).strip()
        links.append({"text": text, "url": lm.group(1)})
    if not links:
        for lm in re.finditer(r"""href=["']([^"']+)["']""", content_html):
            links.append({"text": "", "url": lm.group(1)})
    out["links"] = links
    return out


def main():
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    results = {}
    for name, code in SCHOOLS:
        if only and name not in only and code not in only:
            continue
        try:
            html = fetch(f"https://bm.chsi.com.cn/jcxkzs/sch/{code}", f"chsi_{code}.html")
            info = parse_chsi(html)
        except Exception as e:
            info = {"error": f"{type(e).__name__} {e}"}
        results[name] = {"code": code, **info}
        title = info.get("title", "")
        t = info.get("time", "")
        links = info.get("links", [])
        print(f"[{name}] {title} | 报名 {t}")
        for l in links:
            print(f"    -> {l['url']}  ({l['text'][:30]})")
        if info.get("error"):
            print("    ERROR:", info["error"])
        time.sleep(0.3)
    (CACHE / "chsi_index.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n已缓存到", CACHE / "chsi_index.json", "共", len(results), "校")


if __name__ == "__main__":
    main()
