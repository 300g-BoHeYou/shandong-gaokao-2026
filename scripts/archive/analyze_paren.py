# -*- coding: utf-8 -*-
"""分析志愿类名称括号内容, 评估"括号内列出专业"的提取可行性。"""
import json
import re
from collections import Counter

import pandas as pd

df = pd.read_excel("2026山东高考第一批次投档.xlsx", sheet_name="第一次投档表", dtype=str)


def parse(name):
    m = re.match(r"^([0-9A-Za-z]{1,4})\s+(.*)$", str(name).strip())
    return m.group(2) if m else str(name).strip()


def core(n):
    return re.sub(r"[（(].*$", "", n).strip()


df["专业名"] = df["专业代号及名称"].apply(parse)
df["核心"] = df["专业名"].apply(core)

with open("软科中国大学专业排名_2026.json", encoding="utf-8") as f:
    data = json.load(f)

all_major_names = {code_name.split(" ", 1)[1] if " " in code_name else code_name for cls in data.values() for code_name in cls}
lei_names = {lei for cls in data.values() for lei in cls}

paren = df["专业名"].str.extract(r"[（(](.*)[)）]$")[0]
has_paren = df[paren.notna()].copy()
has_paren["paren"] = paren[paren.notna()]
print("含括号的行数:", len(has_paren), "/", len(df))

# 括号内容分类
kw_cnt = Counter()
contains_major = 0
samples_yes = []
samples_no = []
for _, r in has_paren.iterrows():
    t = r["paren"]
    items = [x.strip() for x in re.split(r"[、,，;；/]", t)]
    known = [it for it in items if it in all_major_names or it in lei_names or it + "类" in lei_names]
    if known:
        contains_major += 1
        if len(samples_yes) < 15:
            samples_yes.append((r["专业名"], known))
    else:
        if len(samples_no) < 15:
            samples_no.append((r["专业名"], t))

print("括号内可直接匹配到专业/专业类的行数:", contains_major)
print("\n== 能匹配的样本 ==")
for s in samples_yes:
    print("  ", s)
print("\n== 不能直接匹配的样本(说明性括号) ==")
for s in samples_no:
    print("  ", s)

# 各类说明性关键词
for kw in ["含", "试验班", "实验班", "基地班", "卓越", "试点", "中外", "双学位", "定向", "公费", "拔尖", "本硕", "本博", "师范", "联合培养"]:
    print(kw, has_paren["paren"].str.contains(kw).sum())
