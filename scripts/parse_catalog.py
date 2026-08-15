# -*- coding: utf-8 -*-
"""解析本科专业目录 PDF -> JSON 树; 并做 目录 vs 软科838 vs 投档表 的对照。"""
import json
import re

import pdfplumber

# ---------- 1. 解析 PDF ----------
men = None
lei = None
tree = {}          # 门类 -> {专业类: [(code,name),...]}
men_order = []
lei_order = []
code2name = {}
name2codes = {}

with pdfplumber.open("本科专业目录.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text() or ""
        for raw in text.split("\n"):
            line = raw.strip()
            if not line:
                continue
            m = re.match(r"^(\d{2})\s*学科门类[：:]\s*(.+)$", line)
            if m:
                men = m.group(2).strip()
                lei = None
                if men not in men_order:
                    men_order.append(men)
                tree.setdefault(men, {})
                continue
            m = re.match(r"^(\d{4})\s*([^\d].+)$", line)
            if m:
                lei = m.group(2).strip()
                if men is None:
                    men = "未知门类"
                if lei not in lei_order:
                    lei_order.append(lei)
                tree.setdefault(men, {}).setdefault(lei, [])
                continue
            # 专业代码: 5-8位数字 + 可选 T/K 后缀 (如 0502100T, 140002TK)
            m = re.match(r"^(\d{5,8}[A-Z]*)\s*([^\d].*)$", line)
            if m:
                code, name = m.group(1).strip(), m.group(2).strip()
                name = re.sub(r"（注[：:].*$", "", name).strip()
                if men is None:
                    men = "未知门类"
                if lei is None:
                    lei = "（不分专业类）"   # 如交叉学科门类下无专业类分组
                    if lei not in lei_order:
                        lei_order.append(lei)
                    tree.setdefault(men, {}).setdefault(lei, [])
                tree[men][lei].append((code, name))
                code2name[code] = name
                name2codes.setdefault(name, []).append(code)
                continue

total = sum(len(v) for c in tree.values() for v in c.values())
print("门类数:", len(men_order))
print("专业类数:", len(lei_order))
print("专业总数:", total)

with open("scripts/catalog_tree.json", "w", encoding="utf-8") as f:
    json.dump({"men_order": men_order, "lei_order": lei_order, "tree": tree}, f, ensure_ascii=False, indent=1)

# ---------- 2. 对照: 软科838 vs 目录 ----------
with open("软科中国大学专业排名_2026.json", encoding="utf-8") as f:
    ruanke = json.load(f)

rk_majors = {}
for men_, cls in ruanke.items():
    for lei_, majors in cls.items():
        for code_name, ranks in majors.items():
            code = code_name.split(" ")[0] if " " in code_name else ""
            name = code_name.split(" ", 1)[1] if " " in code_name else code_name
            rk_majors[code_name] = {"code": code, "name": name, "men": men_, "lei": lei_, "ranks": ranks}

print("\n软科专业数:", len(rk_majors))

# 软科专业名 vs 目录名
rk_names = {v["name"] for v in rk_majors.values()}
cat_names = set(name2codes.keys())
in_cat = rk_names & cat_names
not_in_cat = sorted(rk_names - cat_names)
print("软科专业名在目录2025中的:", len(in_cat))
print("软科专业名不在目录2025中的:", len(not_in_cat))
for n in not_in_cat[:50]:
    print("   软科有/目录无:", n)

# 目录中但软科未发布(838)的专业
cat_not_rk = sorted(cat_names - rk_names)
print("\n目录2025有但软科2026未发布的专业名:", len(cat_not_rk))
for n in cat_not_rk[:80]:
    print("   目录有/软科无:", n)
