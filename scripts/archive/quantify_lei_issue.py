# -*- coding: utf-8 -*-
"""量化大类展开问题: 目录全集 vs 该校实际开设(软科收录∪投档直接∪试验班查证) 交集。"""
import json
import re
from collections import Counter

import pandas as pd

# 软科: 学校 -> 开设专业名集合
with open("软科中国大学专业排名_2026.json", encoding="utf-8") as f:
    ruanke = json.load(f)
rk_open = {}
for men, cls in ruanke.items():
    for lei, majors in cls.items():
        for code_name, ranks in majors.items():
            name = code_name.split(" ", 1)[1] if " " in code_name else code_name
            for school in ranks:
                rk_open.setdefault(school, set()).add(name)

# 目录
with open("scripts/catalog_tree.json", encoding="utf-8") as f:
    cat = json.load(f)
cat_names = set()
for cls in cat["tree"].values():
    for lei, majors in cls.items():
        for _c, nm in majors:
            cat_names.add(nm)

# 投档表直接招生 + 试验班查证
td = pd.read_excel("2026山东高考第一批次投档.xlsx", sheet_name="第一次投档表", dtype=str)
syb = json.load(open("scripts/syb_data.json", encoding="utf-8"))

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

direct_open = {}   # 学校 -> 直接招生专业名
for _, r in td.iterrows():
    _c, full = parse_name(r["专业代号及名称"])
    core, _n = split_core_note(full)
    _s, school = school_parts(r["院校代号及名称"])
    if core in cat_names:
        direct_open.setdefault(school, set()).add(core)
    key = f"{_s}|{full}|{str(r['最低位次']).strip()}"
    if key in syb and syb[key]["mode"] == "list":
        direct_open.setdefault(school, set()).update(syb[key]["majors"])

def school_open(school):
    s = set(rk_open.get(school, set()))
    s |= direct_open.get(school, set())
    return s

# 软科树的 专业类 -> keys (同 build)
lei2major = {}
for men, cls in ruanke.items():
    for lei, majors in cls.items():
        lei2major.setdefault(lei, [])
        for code_name in majors:
            lei2major[lei].append(code_name)

TEST_BAN = re.compile(r"试验班|实验班|试点班")
stats = {"rows": 0, "empty": 0, "reduced": 0, "unchanged": 0}
empty_samples = []
examples = []
all_reduction = []
for _, r in td.iterrows():
    _c, full = parse_name(r["专业代号及名称"])
    core, _n = split_core_note(full)
    _s, school = school_parts(r["院校代号及名称"])
    if core not in lei2major:
        continue
    stats["rows"] += 1
    catalog_keys = lei2major[core]
    cat_n = len(catalog_keys)
    opened = school_open(school)
    kept = [k for k in catalog_keys if (k.split(" ", 1)[1] if " " in k else k) in opened]
    if not kept:
        stats["empty"] += 1
        if len(empty_samples) < 8:
            empty_samples.append((school, core, cat_n, "软科收录" if school in rk_open else "软科未收录"))
    elif len(kept) < cat_n:
        stats["reduced"] += 1
        all_reduction.append((cat_n, len(kept)))
    else:
        stats["unchanged"] += 1
    if len(examples) < 6 and school == "清华大学" and core in ("计算机类", "临床医学类"):
        examples.append((school, core, cat_n, sorted(k.split(" ", 1)[1] if " " in k else k for k in kept)))

print("大类招生行总数:", stats["rows"])
print("交集后减少:", stats["reduced"], " 不变(该校全开):", stats["unchanged"], " 交集为空(回退目录):", stats["empty"])
if all_reduction:
    avg_before = sum(a for a, b in all_reduction) / len(all_reduction)
    avg_after = sum(b for a, b in all_reduction) / len(all_reduction)
    print(f"减少行的平均: 目录{avg_before:.1f} -> 实际开设{avg_after:.1f} 个专业")
print("\n交集为空的样例(将回退目录全集):")
for s in empty_samples:
    print("  ", s)
print("\n抽查(清华):")
for s in examples:
    print(f"  {s[0]} {s[1]}: 目录{s[2]} -> 实际{s[3]}")
