# -*- coding: utf-8 -*-
"""统计其余软科未收录院校的大类行数量, 决定是否生成查证表。"""
import json
import re
from collections import Counter

import pandas as pd

with open("软科中国大学专业排名_2026.json", encoding="utf-8") as f:
    ruanke = json.load(f)
rk_schools = {s for m in ruanke.values() for cls in m.values() for rks in cls.values() for s in rks}

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
    if school not in rk_schools and core in lei_names:
        schools.setdefault(school, []).append(full)

total = sum(len(v) for v in schools.values())
print("其余未收录院校中, 有大类行的院校数:", len(schools), " 大类行总数:", total)
print("\n按院校:")
for s, rows in sorted(schools.items(), key=lambda x: -len(x[1])):
    print(f"  {len(rows)}× {s}: {', '.join(rows[:6])}{' …' if len(rows) > 6 else ''}")

# 对比: 已处理(国防科大/社科院)
print("\n已处理: 国防科技大学 5 行, 中国社会科学院大学 1 行")
