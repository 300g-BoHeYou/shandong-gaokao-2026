# -*- coding: utf-8 -*-
"""修正统计: 校区回退后, 真正未收录且有大类行的院校。"""
import json
import re
from collections import Counter

import pandas as pd

with open("软科中国大学专业排名_2026.json", encoding="utf-8") as f:
    ruanke = json.load(f)
rk_schools = {s for m in ruanke.values() for cls in m.values() for rks in cls.values() for s in rks}
rk_norm = {}
for s in rk_schools:
    key = re.sub(r"\s+", "", s).replace("（", "(").replace("）", ")")
    rk_norm.setdefault(key, s)

SUFFIX = [
    r"克拉玛依校区$", r"秦皇岛分校$", r"威海分校$", r"青岛校区$", r"济南校区$",
    r"医学部$", r"医学院$", r"[（(][^（()）]*校区[）)]$", r"[（(][^（()）]*分校[）)]$",
    r"[（(][^（()）]*[）)]$",
]


def canon(name):
    n = re.sub(r"\s+", "", name).replace("（", "(").replace("）", ")")
    if n in rk_norm:
        return True
    cur = n
    for _ in range(4):
        nxt = cur
        for pat in SUFFIX:
            n2 = re.sub(pat, "", nxt)
            if n2 != nxt and n2 in rk_norm:
                return True
        if nxt == cur:
            break
        cur = nxt
    return False


with open("scripts/catalog_tree.json", encoding="utf-8") as f:
    cat = json.load(f)
lei_names = set()
for cls in cat["tree"].values():
    for lei in cls:
        lei_names.add(lei)

td = pd.read_excel("2026山东高考第一批次投档.xlsx", sheet_name="第一次投档表", dtype=str)


def parse_name(name):
    m = re.match(r"^([0-9A-Za-z]{1,4})\s+(.*)$", str(name).strip())
    return (m.group(1), m.group(2).strip()) if m else ("", str(name).strip())


def split_core_note(full):
    m = re.search(r"[（(]", full)
    if m:
        return full[: m.start()].strip(), full[m.start() + 1:].rstrip(")）").strip()
    return full, ""


def school_parts(s):
    m = re.match(r"^([0-9A-Za-z]+)(.*)$", str(s).strip())
    if m and m.group(1) and m.group(2):
        return m.group(1), m.group(2).strip()
    return "", str(s).strip()


schools = {}
for _, r in td.iterrows():
    _c, full = parse_name(r["专业代号及名称"])
    core, _n = split_core_note(full)
    sc, school = school_parts(r["院校代号及名称"])
    if canon(school):
        continue  # 校区回退后已收录
    if core in lei_names:
        schools.setdefault(school, []).append((full, str(r["最低位次"])))

total = sum(len(v) for v in schools.values())
print("校区回退后, 真正未收录且有大类行的院校数:", len(schools), " 大类行总数:", total)
for s, rows in sorted(schools.items()):
    for full, rank in rows:
        print(f"  {s} | {full} | {rank}名")
