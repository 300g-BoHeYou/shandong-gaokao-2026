# -*- coding: utf-8 -*-
"""检查 chsi 报名平台页 content 字段长度(可能内联简章正文)。"""
import json
import re
from pathlib import Path

CACHE = Path(__file__).resolve().parent.parent / "qj_cache"


def js_unescape(s):
    s = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)
    for a, b in [('\\"', '"'), ("\\'", "'"), ("\\/", "/"), ("\\n", "\n"), ("\\r", ""), ("\\t", " "), ("\\\\", "\\")]:
        s = s.replace(a, b)
    return s


def strip(h):
    h = re.sub(r"<[^>]+>", " ", h)
    h = h.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", h).strip()


idx = json.loads((CACHE / "chsi_index.json").read_text(encoding="utf-8"))
longs = []
for name, info in idx.items():
    code = info["code"]
    p = CACHE / f"chsi_{code}.html"
    if not p.exists():
        print(f"[{name}] 缺缓存")
        continue
    html = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'content:\s*"((?:[^"\\]|\\.)*)"', html, re.S)
    raw = js_unescape(m.group(1)) if m else ""
    text = strip(raw)
    flag = "★" if len(text) > 300 else " "
    print(f"{flag}[{name}] content {len(raw):>6}B 文本 {len(text):>5}字  {text[:90]}")
    if len(text) > 300:
        longs.append((name, text))
print("\n内联长文本校数:", len(longs))
