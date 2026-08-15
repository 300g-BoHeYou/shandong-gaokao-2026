# -*- coding: utf-8 -*-
"""检查用户填好的试验班查证清单: 填写率、格式、特殊标记。"""
import re
from collections import Counter

import pandas as pd

XLSX = "试验班查证清单.xlsx"
df = pd.read_excel(XLSX, dtype=str)
print("行数:", len(df), " 列:", list(df.columns))

# 包含专业列
col = "包含专业(顿号分隔,待填)"
filled = df[df[col].notna() & (df[col].str.strip() != "")]
print("\n已填行数:", len(filled), " /", len(df))

# 填写内容分析
vals = filled[col].astype(str).str.strip()
len_dist = vals.str.len().describe()
print("\n填写内容长度分布:\n", len_dist)

# 特殊标记检测
special_kw = ["任选", "全部", "不限", "所有", "未查到", "官网", "任意", "各专业", "专业不限", "自选", "任选一"]
print("\n含特殊关键词的行:")
for kw in special_kw:
    hits = vals[vals.str.contains(kw, na=False)]
    if len(hits):
        print(f"  [{kw}] {len(hits)} 行, 样例:")
        for i, (idx, v) in enumerate(hits.items()):
            if i >= 3:
                print("    ...")
                break
            row = df.loc[idx]
            print(f"    {row['院校名称']} | {row['志愿类全名']} | 填写: {v[:80]}")

# 填写内容样例(前15条非空)
print("\n填写内容样例:")
n = 0
for _, r in df.iterrows():
    v = str(r[col]).strip() if pd.notna(r[col]) else ""
    if v:
        print(f"  {r['院校名称']} {r['志愿类全名']} -> {v[:70]}")
        n += 1
        if n >= 15:
            break

# 未填行分布
unfilled = df[df[col].isna() | (df[col].str.strip() == "")]
print("\n未填行数:", len(unfilled))
if len(unfilled):
    print("未填行(院校):")
    for s, c in Counter(unfilled["院校名称"]).most_common():
        print(f"  {c}× {s}")

# 填写的专业名与目录对照
import json
with open("scripts/catalog_tree.json", encoding="utf-8") as f:
    cat = json.load(f)
cat_names = set()
for cls in cat["tree"].values():
    for lei, majors in cls.items():
        for _code, nm in majors:
            cat_names.add(nm)

all_filled_terms = set()
for v in vals:
    for t in re.split(r"[、,，;；/]", v):
        t = t.strip()
        if t:
            all_filled_terms.add(t)
print("\n填写的去重专业词条数:", len(all_filled_terms))
not_in_cat = sorted(t for t in all_filled_terms if t not in cat_names and not any(k in t for k in special_kw))
print("不在目录2026中的词条:", len(not_in_cat))
for t in not_in_cat[:60]:
    print("  ", t)
