# -*- coding: utf-8 -*-
"""分析投档表与软科数据：院校名、专业名、匹配度。"""
import json
import re

import pandas as pd

df = pd.read_excel("2026山东高考第一批次投档.xlsx", sheet_name="第一次投档表", dtype=str)
schools = df["院校代号及名称"].str.replace(r"^[0-9A-Za-z]+", "", regex=True).unique()
print("== 投档表院校名含括号 ==")
for s in sorted(schools):
    if "(" in s or "（" in s:
        print(repr(s))
print("total schools:", len(schools))

with open("软科中国大学专业排名_2026.json", encoding="utf-8") as f:
    data = json.load(f)
rk_schools = set()
for _men, cls in data.items():
    for _c, majors in cls.items():
        for _m, ranks in majors.items():
            rk_schools.update(ranks.keys())
print()
print("软科学校数:", len(rk_schools))
print("== 软科学校名含括号 ==")
for s in sorted(rk_schools):
    if "(" in s or "（" in s:
        print(repr(s))
