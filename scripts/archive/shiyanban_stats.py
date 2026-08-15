# -*- coding: utf-8 -*-
"""统计312个试验班志愿类的院校分布, 供方案设计参考。"""
import re
from collections import Counter

import pandas as pd

df = pd.read_excel("2026山东高考第一批次投档.xlsx", sheet_name="第一次投档表", dtype=str)


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


TEST_BAN = re.compile(r"试验班|实验班|试点班")
rows = []
for _, r in df.iterrows():
    code, full = parse_name(r["专业代号及名称"])
    core, note = split_core_note(full)
    if not TEST_BAN.search(core):
        continue
    sc, school = school_parts(r["院校代号及名称"])
    rows.append({
        "sc": sc, "school": school, "full": full, "core": core, "note": note,
        "xk": str(r["选考科目要求"]).strip(),
        "score": str(r["最低分"]), "rank": str(r["最低位次"]),
        "typ": str(r["专项计划/中外合作"]).strip() if pd.notna(r["专项计划/中外合作"]) else "普通",
    })

print("试验班志愿类总数:", len(rows))
schools = Counter(r["school"] for r in rows)
print("涉及院校数:", len(schools))
print("\n按院校的试验班行数 (top 25):")
for s, c in schools.most_common(25):
    print(f"  {c}× {s}")

# 试验班名称 × 院校组合(查证单位)
units = Counter((r["school"], r["full"]) for r in rows)
print("\n查证单位数(院校×志愿类全名, 去重):", len(units))
# 同校同名试验班重复行(可能是普通+专项并存)
dup = {k: v for k, v in units.items() if v > 1}
print("同校同全名重复行数:", len(dup))

# 位次范围
ranks = sorted(int(r["rank"]) for r in rows if r["rank"].isdigit())
print("\n位次范围:", ranks[0], "-", ranks[-1], " 中位数:", ranks[len(ranks) // 2])

# 顶尖院校(位次<5000)的行数
top = [r for r in rows if r["rank"].isdigit() and int(r["rank"]) < 5000]
print("位次<5000的试验班行数:", len(top), " 涉及院校:", len(set(r["school"] for r in top)))

# 各试验班名称分布
print("\n核心名分布:")
for n, c in Counter(r["core"] for r in rows).most_common():
    print(f"  {c}× {n}")
