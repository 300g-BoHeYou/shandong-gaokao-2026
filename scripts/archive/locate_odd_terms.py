# -*- coding: utf-8 -*-
"""定位填写中的异常词条所在行与上下文, 供确认修正方案。"""
import re

import pandas as pd

df = pd.read_excel("试验班查证清单.xlsx", dtype=str)
col = "包含专业(顿号分隔,待填)"

import json
with open("scripts/catalog_tree.json", encoding="utf-8") as f:
    cat = json.load(f)
cat_names = set()
for cls in cat["tree"].values():
    for lei, majors in cls.items():
        for _code, nm in majors:
            cat_names.add(nm)

# 含顿号的专业名保护(目录中带顿号的专业)
comma_names = sorted(n for n in cat_names if "、" in n)
print("目录中带顿号的专业名:", comma_names)

print("\n== 异常词条所在行 ==")
for _, r in df.iterrows():
    v = str(r[col]).strip() if pd.notna(r[col]) else ""
    if not v:
        continue
    # 先按保护名优先匹配, 再切分
    for t in re.split(r"[、,，;；/]", v):
        t = t.strip()
        if not t or t in cat_names:
            continue
        if any(k in t for k in ["任选", "任意", "全部", "所有", "未查到", "不限"]):
            continue
        # 检查是否含保护名(未切对)
        matched_protect = [p for p in comma_names if p in v]
        print(f"  [{t}] <- {r['院校名称']} | {r['志愿类全名']}")
        if matched_protect:
            print(f"      (该行含带顿号的目录专业: {matched_protect})")
