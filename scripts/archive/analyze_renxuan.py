# -*- coding: utf-8 -*-
"""分析任选标记行、未填行, 并验证'该校开设专业'可从投档表推导。"""
import re
from collections import Counter

import pandas as pd

df = pd.read_excel("试验班查证清单.xlsx", dtype=str)
col = "包含专业(顿号分隔,待填)"

print("== 16 个'任选'标记行全文 ==")
for _, r in df.iterrows():
    v = str(r[col]).strip() if pd.notna(r[col]) else ""
    if "任选" in v or "任意" in v:
        print(f"  {r['院校名称']} | {r['志愿类全名']} | 填: {v}")

print("\n== 47 个未填行 ==")
un = df[df[col].isna() | (df[col].str.strip() == "")]
for _, r in un.iterrows():
    print(f"  {r['院校名称']} | {r['志愿类全名']} | {r['选科要求']} | {r['最低分']}分/{r['最低位次']}名")

# 验证: 从投档表推导"该校开设专业"
td = pd.read_excel("2026山东高考第一批次投档.xlsx", sheet_name="第一次投档表", dtype=str)
import json
with open("scripts/catalog_tree.json", encoding="utf-8") as f:
    cat = json.load(f)
cat_names = set()
cat_lei_names = set()
for cls in cat["tree"].values():
    for lei, majors in cls.items():
        cat_lei_names.add(lei)
        for _code, nm in majors:
            cat_names.add(nm)

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

school_majors = {}   # 学校 -> 具体专业名集合(直接招生行)
for _, r in td.iterrows():
    _code, full = parse_name(r["专业代号及名称"])
    core, _note = split_core_note(full)
    _sc, school = school_parts(r["院校代号及名称"])
    if core in cat_names:  # 具体专业(非大类)
        school_majors.setdefault(school, set()).add(core)

for s in ["北京大学", "北京理工大学", "清华大学", "西安交通大学", "南开大学", "中国人民大学"]:
    ms = sorted(school_majors.get(s, set()))
    print(f"\n{s}: 投档表直接招生的具体专业数 = {len(ms)}")
    print("  ", "、".join(ms[:40]) + (" …" if len(ms) > 40 else ""))
