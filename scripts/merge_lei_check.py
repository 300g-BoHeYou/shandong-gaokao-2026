# -*- coding: utf-8 -*-
"""
合并《大类查证清单（软科未收录）.xlsx》-> scripts/lei_check.json

键: "院校代码|志愿类全名|最低位次" -> {mode:'list', majors:[专业名,...]} 或 {mode:'notfound'}
"""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SHEET = ROOT / "大类查证清单（软科未收录）.xlsx"
OUT = ROOT / "scripts" / "lei_check.json"

with open(ROOT / "scripts" / "catalog_tree.json", encoding="utf-8") as f:
    cat = json.load(f)
cat_names = set()
for cls in cat["tree"].values():
    for lei, majors in cls.items():
        for _code, nm in majors:
            cat_names.add(nm)
PROTECTED = sorted((n for n in cat_names if "、" in n), key=len, reverse=True)

df = pd.read_excel(SHEET, dtype=str)
col = "包含专业(顿号分隔,待填)"

result = {}
report = {"fixed": [], "unmatched": [], "notfound": [], "empty": []}


def split_majors(text):
    rest = text
    parts = []
    for p in PROTECTED:
        if p in rest:
            parts.append(p)
            rest = rest.replace(p, " ")
    rest = re.sub(r"\s+", "", rest)
    for t in re.split(r"[、,，;；/]", rest):
        t = t.strip()
        if t:
            parts.append(t)
    return parts


for _, r in df.iterrows():
    sc = str(r["院校代码"]).strip()
    full = str(r["志愿类全名"]).strip()
    rank = str(r["最低位次"]).strip()
    key = f"{sc}|{full}|{rank}"
    v = str(r[col]).strip() if pd.notna(r[col]) else ""
    if not v:
        continue
    if "未查到" in v:
        result[key] = {"mode": "notfound"}
        report["notfound"].append(full)
        continue
    majors = []
    for t in split_majors(v):
        if t not in cat_names:
            report["unmatched"].append(f"{full} | 词条[{t}]")
        majors.append(t)
    if not majors:
        report["empty"].append(full)
        continue
    result[key] = {"mode": "list", "majors": majors}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)

print("lei_check.json 条目数:", len(result))
print("未查到:", report["notfound"])
print("无法匹配词条:", report["unmatched"])
print("空:", report["empty"])
