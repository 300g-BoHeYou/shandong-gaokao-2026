# -*- coding: utf-8 -*-
"""
统一合并全部人工查证数据 -> scripts/manual_check.json

数据源:
  1. 试验班查证清单.xlsx             (312 行试验班志愿类)
  2. 大类查证清单（软科未收录）.xlsx   (国防科大/社科院等 6 行)
  3. 大类查证清单（剩余未收录）.xlsx   (重庆外语外事学院 1 行)

输出结构:
{
  "试验班": { "院校代码|志愿类全名|最低位次": {"mode":"list","majors":[...]}
              | {"mode":"renxuan","dir":"理科任选"} | {"mode":"notfound"} },
  "大类":   { "院校代码|志愿类全名|最低位次": {"mode":"list","majors":[...]} | {"mode":"notfound"} }
}
"""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "scripts" / "manual_check.json"
SHEETS = [
    ("试验班", ROOT / "试验班查证清单.xlsx"),
    ("大类", ROOT / "大类查证清单（软科未收录）.xlsx"),
    ("大类", ROOT / "大类查证清单（剩余未收录）.xlsx"),
]

with open(ROOT / "scripts" / "catalog_tree.json", encoding="utf-8") as f:
    cat = json.load(f)
cat_names = set()
for cls in cat["tree"].values():
    for lei, majors in cls.items():
        for _code, nm in majors:
            cat_names.add(nm)
PROTECTED = sorted((n for n in cat_names if "、" in n), key=len, reverse=True)

# 试验班填写中的笔误修正(沿用既往清单)
FIX = {
    "通讯工程": "通信工程",
    "电气工程及自动化": "电气工程及其自动化",
    "电子工程及其自动化": "电气工程及其自动化",
    "储能科学与工程专业": "储能科学与工程",
    "能源与 环境系统工程": "能源与环境系统工程",
    "信息管理与信息系 统": "信息管理与信息系统",
    "集成电路与集成系统": "集成电路设计与集成系统",
    "风景园林学": "风景园林",
    "城市设计专": "城市设计",
    "工程物理（能源实验班）": "工程物理",
    "工程物理(能源实验班)": "工程物理",
    "土木水利与海洋工程": "土木、水利与海洋工程",
    "地理科学类": ["地理科学", "自然地理与资源环境", "人文地理与城乡规划", "地理信息科学"],
    "生物医药工程": "生物医学工程",
    "智能医药工程": "智能医学工程",
    "智能建筑": "智能建造",
    "信息安全应用": "信息安全",
    "水利与交通工程": "土木、水利与交通工程",
    "体育教育与工商管理": ["体育教育", "工商管理"],
}


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


def parse_sheet(path):
    """返回 {key: entry}, key="sc|full|rank"。"""
    df = pd.read_excel(path, dtype=str)
    col = "包含专业(顿号分隔,待填)"
    out = {}
    report = {"fixed": [], "unmatched": [], "notfound": [], "renxuan": []}
    for _, r in df.iterrows():
        sc = str(r["院校代码"]).strip()
        full = str(r["志愿类全名"]).strip()
        rank = str(r["最低位次"]).strip()
        key = f"{sc}|{full}|{rank}"
        v = str(r[col]).strip() if pd.notna(r[col]) else ""
        if not v:
            continue
        if "任选" in v or "任意" in v:
            out[key] = {"mode": "renxuan", "dir": v}
            report["renxuan"].append(f"{r['院校名称']} | {full}")
            continue
        if "未查到" in v:
            out[key] = {"mode": "notfound"}
            report["notfound"].append(f"{r['院校名称']} | {full}")
            continue
        majors = []
        for t in split_majors(v):
            fixed = FIX.get(t)
            if fixed is None:
                fixed = t
                if t not in cat_names:
                    report["unmatched"].append(f"{r['院校名称']} | {full} | 词条[{t}]")
            else:
                report["fixed"].append(f"{r['院校名称']} | {full} | {t} -> {fixed if isinstance(fixed, str) else '、'.join(fixed)}")
            if isinstance(fixed, str):
                majors.append(fixed)
            else:
                majors.extend(fixed)
        seen, majors2 = set(), []
        for m in majors:
            if m not in seen:
                seen.add(m)
                majors2.append(m)
        if majors2:
            out[key] = {"mode": "list", "majors": majors2}
    return out, report


result = {"试验班": {}, "大类": {}}
all_report = {}

for kind, path in SHEETS:
    if not path.exists():
        print(f"跳过(文件不存在): {path}")
        continue
    data, report = parse_sheet(path)
    result[kind].update(data)
    all_report.setdefault(kind, []).append((path.name, report))
    print(f"[{kind}] {path.name}: {len(data)} 条")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print("\n已写出:", OUT)
print("试验班条目:", len(result["试验班"]), " 大类条目:", len(result["大类"]))

for kind, items in all_report.items():
    for fname, rep in items:
        print(f"\n== {kind} · {fname} 报告 ==")
        print("  修正:", len(rep["fixed"]))
        for x in rep["fixed"]:
            print("   ", x)
        print("  无法匹配词条(保留原样):", len(rep["unmatched"]))
        for x in rep["unmatched"]:
            print("   ", x)
        print("  未查到:", len(rep["notfound"]), " 任选:", len(rep["renxuan"]))
