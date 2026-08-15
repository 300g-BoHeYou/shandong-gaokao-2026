# -*- coding: utf-8 -*-
"""验证新 split_core_note 与前端拆分规则对修正后名称的处理。"""
import re

import pandas as pd

df = pd.read_excel("2026山东高考第一批次投档.xlsx", sheet_name="第一次投档表", dtype=str)


def parse_name(name):
    m = re.match(r"^([0-9A-Za-z]{1,4})\s+(.*)$", str(name).strip())
    return (m.group(1), m.group(2).strip()) if m else ("", str(name).strip())


def split_core_note(full):
    m = re.search(r"[（(]", full)
    if m:
        note = full[m.start() + 1:].rstrip(")）")
        return full[: m.start()].strip(), note.strip()
    return full, ""


def split_note(note):
    if not note:
        return []
    t = re.sub(r"[)）]\s*[（(]", "，", note)
    return [s.strip() for s in re.split(r"[，,；;]", t) if s.strip()]


def type_of(r):
    return str(r["专项计划/中外合作"]).strip() if pd.notna(r["专项计划/中外合作"]) else "普通"


tests = [
    "X3 外国语言文学类(含双学士学位项目、外语+财会等实验班选拔，高校专项)",
    "W5 外国语言文学类(含双学士学位)",
    "98 材料科学与工程(中外合作办学)(中南大学和蒙纳士大学中外合作办学项目)",
    "45 数据计算及应用(中外合作办学)(与白俄罗斯格洛德诺杨克库帕尔国立大",
    "0G 外国语言文学类(英语)",
    "59 外国语言文学类(英语和翻译，高校专项计划)",
    "1A 临床医学类(5+3一体化，儿科学)",
    "04 计算机类(高校专项计划)",
]
for v in tests:
    code, full = parse_name(v)
    core, note = split_core_note(full)
    print(f"{v}")
    print(f"   core=[{core}] note=[{note}] -> 拆分 {split_note(note)}")

# 检查 X3 行的 type
print("\nX3 行的 type:")
row = df[df["专业代号及名称"].str.startswith("X3 ", na=False)]
for _, r in row.iterrows():
    print("   ", r["专业代号及名称"], "| type:", type_of(r))
