# -*- coding: utf-8 -*-
import re

import pandas as pd

df = pd.read_excel("2026山东高考第一批次投档.xlsx", sheet_name="第一次投档表", dtype=str)
rows = df[df["专业代号及名称"].str.contains("哲学类", na=False)]
print("含'哲学类'行数:", len(rows))
for v in rows["专业代号及名称"].head(20):
    print(repr(v))

# 检查代号与名称之间分隔符的多样性
samples = df["专业代号及名称"].head(2000)
no_space = [v for v in samples if not re.match(r"^[0-9A-Za-z]{1,4}\s+", str(v).strip())]
print("\n前2000行中非'代号+空格'格式的样本(前30):")
for v in no_space[:30]:
    print(repr(v))
