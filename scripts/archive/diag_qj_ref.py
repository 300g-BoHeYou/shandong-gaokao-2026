# -*- coding: utf-8 -*-
"""诊断: 强基专业为何未匹配到大类参考分。"""
import json
import re

import pandas as pd

with open("scripts/catalog_tree.json", encoding="utf-8") as f:
    cat = json.load(f)
lei2majors = {}
for cls in cat["tree"].values():
    for lei, majors in cls.items():
        lei2majors[lei] = [nm for _c, nm in majors]

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


school_rows = {}
for _, r in td.iterrows():
    _c, full = parse_name(r["专业代号及名称"])
    core, _n = split_core_note(full)
    _s, school = school_parts(r["院校代号及名称"])
    typ = str(r["专项计划/中外合作"]).strip() if pd.notna(r["专项计划/中外合作"]) else "普通"
    try:
        score, rank = int(float(r["最低分"])), int(float(r["最低位次"]))
    except (TypeError, ValueError):
        continue
    school_rows.setdefault(school, []).append((core, score, rank, typ))

for school, major in [("山东大学", "数学与应用数学"), ("中南大学", "数学与应用数学"), ("兰州大学", "化学"),
                      ("厦门大学", "数学类"), ("北京大学", "数学类"), ("复旦大学", "基础医学"),
                      ("华东师范大学", "汉语言文学（古文字学）"), ("中国海洋大学", "海洋科学")]:
    rows = school_rows.get(school, [])
    print(f"\n== {school} / {major} ==  该校志愿类 {len(rows)} 条")
    hit = []
    for core, score, rank, typ in rows:
        mark = ""
        if core == major:
            mark = "  <<< 同名"
        elif core in lei2majors and major in lei2majors[core]:
            mark = "  <<< 大类包含"
        if mark:
            hit.append((core, score, rank, typ))
            print(f"   {core} {score}分/{rank}名 [{typ}]{mark}")
    if not hit:
        # 打印含关键词的志愿类帮助定位
        kw = major[:2]
        near = [f"{c}({s}分,{t})" for c, s, r, t in rows if kw in c][:8]
        print("   未命中; 该校含'%s'的志愿类: %s" % (kw, "、".join(near) or "无"))
