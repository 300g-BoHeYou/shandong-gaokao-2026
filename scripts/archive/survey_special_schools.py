# -*- coding: utf-8 -*-
"""盘点: 中科大是否被软科收录? 国科大/社科院/军校在投档表中有哪些志愿类(特别是大类行)。"""
import json
import re

import pandas as pd

with open("软科中国大学专业排名_2026.json", encoding="utf-8") as f:
    ruanke = json.load(f)
rk_schools = {s for m in ruanke.values() for cls in m.values() for rks in cls.values() for s in rks}

print("中科大在软科收录:", "中国科学技术大学" in rk_schools)
print("国科大在软科收录:", "中国科学院大学" in rk_schools)
print("社科院在软科收录:", "中国社会科学院大学" in rk_schools)

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

# 目标院校: 军校 + 国科大 + 社科院 (+中科大对照)
targets = set()
for s in td["院校代号及名称"]:
    sc, name = school_parts(s)
    if any(k in name for k in ["军", "国防", "警察", "公安"]):
        targets.add(name)
targets |= {"中国科学院大学", "中国社会科学院大学", "中国科学技术大学"}

from collections import Counter
for t in sorted(targets):
    sub = td[td["院校代号及名称"].str.contains(t, na=False)]
    if len(sub) == 0:
        continue
    print(f"\n== {t} ({len(sub)} 行) 软科收录: {t in rk_schools} ==")
    for _, r in sub.iterrows():
        _c, full = parse_name(r["专业代号及名称"])
        core, note = split_core_note(full)
        is_lei = core.endswith("类")
        tag = " [大类]" if is_lei else ""
        print(f"   {full} ｜ {r['选考科目要求']} ｜ {r['最低分']}分/{r['最低位次']}名{tag}")
