# -*- coding: utf-8 -*-
"""深度分析：专业类名/专业名匹配情况。"""
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
df["专业核心"] = df["专业核心2"] = df["专业名"].apply(core)

with open("软科中国大学专业排名_2026.json", encoding="utf-8") as f:
    data = json.load(f)

# 软科树: 门类 -> 专业类 -> "code name" -> {school: rank}
men_leis = Counter()  # 专业类名 -> 出现次数(跨门类)
all_major_names = set()  # 具体专业名(去代码)
major_code_map = {}  # code -> name
for men, cls in data.items():
    for lei, majors in cls.items():
        men_leis[lei] += 1
        for code_name, ranks in majors.items():
            code, name = code_name.split(" ", 1)
            all_major_names.add(name)
            major_code_map[code] = name

print("软科专业类数量(去重):", len(men_leis))
dups = {k: v for k, v in men_leis.items() if v > 1}
print("跨门类重复的专业类名:", dups)

# 投档表中"xx类"核心名
lei_names_td = set(df[df["专业核心"].str.endswith("类")]["专业核心"])
print("\n投档表'xx类'核心名数量:", len(lei_names_td))
match = lei_names_td & set(men_leis)
print("与软科专业类名完全一致的:", len(match))
unmatched = sorted(lei_names_td - set(men_leis))
print("未匹配的'xx类' (前60):")
for u in unmatched[:60]:
    print("  ", u)

# 具体专业匹配
core_names = set(df["专业核心"])
match_major = core_names & all_major_names
print("\n投档表核心名与软科具体专业名完全一致的数量:", len(match_major))
unmatched_major = sorted(core_names - all_major_names)
print("投档表核心名未在软科具体专业中的 (前80):")
for u in unmatched_major[:80]:
    print("  ", u)

# 北京大学医学部 在软科中?
print("\n软科是否含 '北京大学医学部':", "北京大学医学部" in [s for _m, cls in data.items() for _c, ms in cls.items() for _x, rks in ms.items() for s in rks])
for s in sorted({"北京大学", "北京大学医学部", "哈尔滨工业大学", "哈尔滨工业大学（威海）", "哈尔滨工业大学(威海)", "山东大学威海分校", "山东大学（威海）"}):
    print(repr(s), "in 软科:", any(s in rks for _m, cls in data.items() for _c, ms in cls.items() for _x, rks in ms.items()))
