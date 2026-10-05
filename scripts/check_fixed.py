# -*- coding: utf-8 -*-
"""检查修正后的投档表: 原3个截断名现状 + 总行数。"""
import re

import pandas as pd

df = pd.read_excel("2026山东高考第一批次投档.xlsx", sheet_name="第一次投档表", dtype=str)
print("总行数:", len(df))

fulls = [str(v) for v in df["专业代号及名称"]]

print("\n== 含'外国语言文学类(含' 的行 ==")
for v in fulls:
    if "外国语言文学类" in v and "含" in v:
        print("   ", repr(v))

print("\n== 含'蒙纳士' 的行 ==")
for v in fulls:
    if "蒙纳士" in v:
        print("   ", repr(v))

print("\n== 含'格洛德诺' 的行 ==")
for v in fulls:
    if "格洛德诺" in v:
        print("   ", repr(v))

print("\n== 全部截断(括号未闭合)行 ==")
n = 0
for v in fulls:
    v2 = re.sub(r"^[0-9A-Za-z]{1,4}\s+", "", v)
    if ("(" in v2 or "（" in v2) and not re.search(r"[)）]$", v2):
        print("   ", repr(v))
        n += 1
print("   截断行数:", n)

# 数据总行数对比
print("\n院校行数分布(前5):")
print(df["院校代号及名称"].value_counts().head(5).to_string())
