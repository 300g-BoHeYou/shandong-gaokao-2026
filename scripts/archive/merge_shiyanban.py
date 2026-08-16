# -*- coding: utf-8 -*-
"""
合并《试验班查证清单.xlsx》-> scripts/syb_data.json

每行解析为:
  {mode:'list',    majors:[专业名,...]}   具体专业列表
  {mode:'renxuan', dir:'理科任选'}        任选该校开设专业(标注,不展开)
  {mode:'notfound'}                       未查到
空行跳过(保持"未公开")。

键: "院校代码|志愿类全名|最低位次" (吉林大学唐敖庆班同校同名两行靠位次区分)
"""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SHEET = ROOT / "试验班查证清单.xlsx"
OUT = ROOT / "scripts" / "syb_data.json"

with open(ROOT / "scripts" / "catalog_tree.json", encoding="utf-8") as f:
    cat = json.load(f)
cat_names = set()
for cls in cat["tree"].values():
    for lei, majors in cls.items():
        for _code, nm in majors:
            cat_names.add(nm)

# 目录中带顿号的保护名(切分时优先整体提取)
PROTECTED = sorted((n for n in cat_names if "、" in n), key=len, reverse=True)

# 修正映射: (原始 -> 修正名 或 展开列表)
FIX = {
    # ---- 明确笔误 ----
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
    # ---- 建议修正(报告中列出复核) ----
    "生物医药工程": "生物医学工程",
    "智能医药工程": "智能医学工程",
    "智能建筑": "智能建造",
    "信息安全应用": "信息安全",
    "水利与交通工程": "土木、水利与交通工程",
    "体育教育与工商管理": ["体育教育", "工商管理"],
}

df = pd.read_excel(SHEET, dtype=str)
col = "包含专业(顿号分隔,待填)"

result = {}
report = {"renxuan": [], "unfilled": [], "notfound": [], "fixed": [], "unmatched": [], "empty_majors": []}

def split_majors(text):
    """保护名优先整体提取, 其余按顿号/逗号切分。"""
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
        report["unfilled"].append(f"{r['院校名称']} | {full} | {rank}")
        continue
    if "任选" in v or "任意" in v:
        result[key] = {"mode": "renxuan", "dir": v}
        report["renxuan"].append(f"{r['院校名称']} | {full} | {v}")
        continue
    if "未查到" in v:
        result[key] = {"mode": "notfound"}
        report["notfound"].append(f"{r['院校名称']} | {full}")
        continue

    # 具体专业列表
    majors = []
    for t in split_majors(v):
        fixed = FIX.get(t)
        if fixed is None:
            fixed = t
            if t not in cat_names:
                report["unmatched"].append(f"{r['院校名称']} | {full} | 词条[{t}]")
        elif isinstance(fixed, str):
            report["fixed"].append(f"{r['院校名称']} | {full} | {t} -> {fixed}")
        else:
            report["fixed"].append(f"{r['院校名称']} | {full} | {t} -> {'、'.join(fixed)}")
        if isinstance(fixed, str):
            majors.append(fixed)
        else:
            majors.extend(fixed)
    # 修正后去重保序
    seen = set()
    majors2 = []
    for m in majors:
        if m not in seen:
            seen.add(m)
            majors2.append(m)
    if not majors2:
        report["empty_majors"].append(f"{r['院校名称']} | {full}")
        continue
    result[key] = {"mode": "list", "majors": majors2}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)

print("syb_data.json 条目数:", len(result))
print("\n== 任选标注(", len(report["renxuan"]), ") ==")
for x in report["renxuan"]:
    print("  ", x)
print("\n== 未填(", len(report["unfilled"]), ") ==")
for x in report["unfilled"]:
    print("  ", x)
print("\n== 未查到(", len(report["notfound"]), ") ==")
for x in report["notfound"]:
    print("  ", x)
print("\n== 修正(", len(report["fixed"]), ") ==")
for x in report["fixed"]:
    print("  ", x)
print("\n== 无法匹配词条(保留原样, ", len(report["unmatched"]), ") ==")
for x in report["unmatched"]:
    print("  ", x)
print("\n== 解析后为空(", len(report["empty_majors"]), ") ==")
for x in report["empty_majors"]:
    print("  ", x)
