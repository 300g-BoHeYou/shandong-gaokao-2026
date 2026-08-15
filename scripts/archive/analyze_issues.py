# -*- coding: utf-8 -*-
"""综合分析: 问题1-4 的影响面统计 + 特色专业验证 + 目录对照。"""
import json
import re
from collections import Counter

import pandas as pd

# ---------- 数据 ----------
df = pd.read_excel("2026山东高考第一批次投档.xlsx", sheet_name="第一次投档表", dtype=str)

def parse_name(name):
    m = re.match(r"^([0-9A-Za-z]{1,4})\s+(.*)$", str(name).strip())
    return (m.group(1), m.group(2).strip()) if m else ("", str(name).strip())

def split_core_note(full):
    m = re.search(r"[（(](.*)[)）]$", full)
    if m:
        return full[: m.start()].strip(), m.group(1).strip()
    return full, ""

rows = []
for _, r in df.iterrows():
    code, full = parse_name(r["专业代号及名称"])
    core, note = split_core_note(full)
    typ = str(r["专项计划/中外合作"]).strip() if pd.notna(r["专项计划/中外合作"]) else "普通"
    rows.append({"code": code, "core": core, "note": note, "typ": typ,
                 "xk": str(r["选考科目要求"]).strip(), "school": str(r["院校代号及名称"])})

with open("软科中国大学专业排名_2026.json", encoding="utf-8") as f:
    ruanke = json.load(f)

rk_majors = {}
for men, cls in ruanke.items():
    for lei, majors in cls.items():
        for code_name, ranks in majors.items():
            name = code_name.split(" ", 1)[1] if " " in code_name else code_name
            rk_majors[code_name] = {"name": name, "men": men, "lei": lei, "ranks": ranks}

with open("scripts/catalog_tree.json", encoding="utf-8") as f:
    cat = json.load(f)
cat_tree = cat["tree"]
cat_names = set()
cat_lei_names = set()
for cls in cat_tree.values():
    for lei, majors in cls.items():
        cat_lei_names.add(lei)
        for _code, name in majors:
            cat_names.add(name)

# ---------- 1. 特色专业验证 ----------
special = {}
for key, v in rk_majors.items():
    vals = set(v["ranks"].values())
    if vals == {1}:
        special[key] = v
print("== 特色专业(所有学校排名=1) ==")
print("专业数:", len(special))
total_pts = sum(len(v["ranks"]) for v in special.values())
schools = {s for v in special.values() for s in v["ranks"]}
print("特色专业点数:", total_pts, " 涉及高校:", len(schools), " (方法论: 333点/179校)")
print("特色专业名单:")
for k, v in sorted(special.items(), key=lambda x: x[1]["men"]):
    print("   ", k, "(", v["men"], "·", v["lei"], ")", len(v["ranks"]), "校")

# ---------- 2. 问题1: 备注与类型重复 ----------
dup = [r for r in rows if r["note"] and r["typ"] != "普通" and r["note"] == r["typ"]]
print("\n== 问题1: note 与 type 完全重复的行 ==", len(dup))
dup2 = [r for r in rows if r["note"] and r["typ"] != "普通" and r["typ"] in r["note"].split("，")]
print("note 含 type 的行(拆逗号后):", len(dup2))
for r in dup2[:10]:
    print("   ", r["school"], "|", r["core"], "| note:", r["note"], "| type:", r["typ"])

# ---------- 3. 问题3: 括号备注含多个片段 ----------
multi = [r for r in rows if r["note"] and re.search(r"[，,；;]", r["note"])]
print("\n== 问题3: note 含逗号/分号的行 ==", len(multi))
cnt = Counter()
for r in multi:
    cnt[r["note"]] += 1
print("去重后的备注文本数:", len(cnt))
for note, c in cnt.most_common(25):
    print("   ", c, "×", note)

# ---------- 4. 问题4: 试验班/缺少具体专业统计 ----------
TEST_BAN = re.compile(r"试验班|实验班|试点班")
test_rows = [r for r in rows if TEST_BAN.search(r["core"])]
print("\n== 问题4: 试验班/实验班/试点班 志愿类 ==")
print("行数(志愿类数):", len(test_rows), " / 总行数:", len(rows))
names = Counter(r["core"] for r in test_rows)
print("去重核心名数:", len(names))
for n, c in names.most_common(40):
    print("   ", c, "×", n)
# 无映射但非试验班(伪key)的
others = [r for r in rows if not TEST_BAN.search(r["core"]) and not r["core"].endswith("类") and r["core"] not in cat_names]
print("\n非试验班、非目录专业名的志愿类(职业本科等): 行数", len(others), " 去重名数", len(set(r["core"] for r in others)))
for n, c in Counter(r["core"] for r in others).most_common(30):
    print("   ", c, "×", n)

# ---------- 5. 投档表核心名 vs 目录 ----------
core_set = set(r["core"] for r in rows)
in_cat_major = core_set & cat_names
in_cat_lei = core_set & cat_lei_names
print("\n== 投档表核心名 vs 目录 ==")
print("在目录中为具体专业:", len(in_cat_major))
print("在目录中为专业类:", len(in_cat_lei))
not_found = sorted(core_set - cat_names - cat_lei_names)
print("目录中未找到:", len(not_found))
for n in not_found[:60]:
    print("   ", n)

# ---------- 6. 投档表中属于"软科未发布7专业"的行 ----------
rk_names = {v["name"] for v in rk_majors.values()}
unranked7 = sorted(cat_names - rk_names)
print("\n目录有/软科无(7个):", unranked7)
hit7 = [r for r in rows if r["core"] in unranked7]
print("投档表中命中这7个专业的志愿类行数:", len(hit7))
for r in hit7:
    print("   ", r["school"], "|", r["core"])
