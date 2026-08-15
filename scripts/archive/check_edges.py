# -*- coding: utf-8 -*-
"""检查异常名称行 与 备注/类型 交叉情况。"""
import re

import pandas as pd

df = pd.read_excel("2026山东高考第一批次投档.xlsx", sheet_name="第一次投档表", dtype=str)

def parse_name(name):
    m = re.match(r"^([0-9A-Za-z]{1,4})\s+(.*)$", str(name).strip())
    return (m.group(1), m.group(2).strip()) if m else ("", str(name).strip())

def split_core_note(full):
    m = re.search(r"[（(](.*)[)）]$", full)
    if m:
        return full[: m.start()].strip(), m.group(1).strip()
    return full, ""

# 1. "外国语言文学类(含…" 原始行
print("== 含'外国语言文学类'的原始行 ==")
for v in df[df["专业代号及名称"].str.contains("外国语言文学类", na=False)]["专业代号及名称"]:
    print("   ", repr(v))

# 2. 括号未闭合/括号后有内容 的行
print("\n== 括号不在末尾或未闭合的行 ==")
cnt = 0
for v in df["专业代号及名称"]:
    full = parse_name(v)[1]
    if "(" in full or "（" in full:
        if not re.search(r"[（(](.*)[)）]$", full):
            print("   ", repr(v))
            cnt += 1
            if cnt > 12:
                break
print("   ... 前12条, 共", end=" ")

# 3. note 含'中外合作' 但 type 非中外合作办学
print("\n== note含中外合作 但 type 不是中外合作办学 ==")
n = 0
for _, r in df.iterrows():
    code, full = parse_name(r["专业代号及名称"])
    core, note = split_core_note(full)
    typ = str(r["专项计划/中外合作"]).strip() if pd.notna(r["专项计划/中外合作"]) else "普通"
    if "中外合作" in note and typ != "中外合作办学":
        print("   ", r["院校代号及名称"], "|", full, "| type:", typ)
        n += 1
        if n > 10:
            break
print("   共匹配行数:", n, "+")

# 4. note == '中外合作办学' 且 type=='中外合作办学' 的行数
m4 = df.apply(lambda r: (split_core_note(parse_name(r["专业代号及名称"])[1])[1] == "中外合作办学"
             and str(r["专项计划/中外合作"]).strip() == "中外合作办学"), axis=1).sum()
print("\nnote与type都是'中外合作办学'的行数:", m4)
