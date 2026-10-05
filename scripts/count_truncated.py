# -*- coding: utf-8 -*-
"""统计投档表中名称截断(括号未闭合/括号后仍有内容)的行。"""
import re

import pandas as pd

df = pd.read_excel("2026山东高考第一批次投档.xlsx", sheet_name="第一次投档表", dtype=str)


def parse_name(name):
    m = re.match(r"^([0-9A-Za-z]{1,4})\s+(.*)$", str(name).strip())
    return (m.group(1), m.group(2).strip()) if m else ("", str(name).strip())


truncated = []
for _, r in df.iterrows():
    code, full = parse_name(r["专业代号及名称"])
    # 括号不闭合: 有 ( 或 （ 但结尾不是 ) 或 ）
    if ("(" in full or "（" in full) and not re.search(r"[)）]$", full):
        truncated.append((full, r["院校代号及名称"]))

print("截断行数:", len(truncated))
from collections import Counter
c = Counter(t[0] for t in truncated)
print("去重名称数:", len(c))
for name, n in c.most_common(40):
    print(f"   {n} × {name}")

# 截断影响: 取第一个'('前为潜在核心名, 看能否匹配目录
import json
with open("scripts/catalog_tree.json", encoding="utf-8") as f:
    cat = json.load(f)
cat_names = set()
for cls in cat["tree"].values():
    for lei, majors in cls.items():
        for _code, nm in majors:
            cat_names.add(nm)
for name, n in c.most_common():
    core0 = re.split(r"[（(]", name)[0].strip()
    print(f"   潜在核心名[{core0}] 在目录中: {core0 in cat_names}  ({n}×)")
