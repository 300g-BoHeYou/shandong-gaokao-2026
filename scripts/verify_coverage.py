# -*- coding: utf-8 -*-
"""验证: 软科收录的该校专业 + 投档表直接招生专业 = 该校开设专业(近似)。
检查清华/北大等'任选'标记校的覆盖度。"""
import json
import re

import pandas as pd

with open("软科中国大学专业排名_2026.json", encoding="utf-8") as f:
    ruanke = json.load(f)

# 软科: 学校名 -> {专业名}
rk_school_majors = {}
for men, cls in ruanke.items():
    for lei, majors in cls.items():
        for code_name, ranks in majors.items():
            name = code_name.split(" ", 1)[1] if " " in code_name else code_name
            for school in ranks:
                rk_school_majors.setdefault(school, set()).add(name)

# 投档表直接招生专业
td = pd.read_excel("2026山东高考第一批次投档.xlsx", sheet_name="第一次投档表", dtype=str)
with open("scripts/catalog_tree.json", encoding="utf-8") as f:
    cat = json.load(f)
cat_names = set()
for cls in cat["tree"].values():
    for lei, majors in cls.items():
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

td_majors = {}
for _, r in td.iterrows():
    _c, full = parse_name(r["专业代号及名称"])
    core, _n = split_core_note(full)
    _s, school = school_parts(r["院校代号及名称"])
    if core in cat_names:
        td_majors.setdefault(school, set()).add(core)

for s in ["清华大学", "北京大学", "北京理工大学", "华南理工大学", "厦门大学", "同济大学",
          "哈尔滨工业大学", "浙江大学", "北京科技大学", "上海交通大学", "复旦大学", "西安交通大学"]:
    rk = rk_school_majors.get(s, set())
    tdset = td_majors.get(s, set())
    union = rk | tdset
    print(f"{s}: 软科收录 {len(rk)} 个专业 | 投档直接 {len(tdset)} | 并集 {len(union)}")
    if s == "清华大学":
        print("  清华软科专业样例:", "、".join(sorted(rk)[:30]))
