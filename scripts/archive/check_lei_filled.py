# -*- coding: utf-8 -*-
"""检查填写好的《大类查证清单(软科未收录)》内容。"""
import pandas as pd

df = pd.read_excel("大类查证清单（软科未收录）.xlsx", dtype=str)
col = "包含专业(顿号分隔,待填)"
print("行数:", len(df))
for _, r in df.iterrows():
    v = str(r[col]).strip() if pd.notna(r[col]) else "(未填)"
    print(f"  {r['院校代码']} {r['志愿类全名']} ｜ {r['最低位次']}名 ｜ 填: {v}")
