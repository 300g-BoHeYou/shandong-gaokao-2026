# -*- coding: utf-8 -*-
"""由 scripts/catalog_tree.json 生成前端三级目录 data_catalog.js
   window.CAT2026 = { men:[门类顺序], tree:{门类:{专业类:[专业名,...]}}, major2:{专业名:[门类,专业类]} }
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
with open(ROOT / "scripts" / "catalog_tree.json", encoding="utf-8") as f:
    cat = json.load(f)

tree, men_order, major2 = {}, [], {}
for men, cls in cat["tree"].items():
    men_order.append(men)
    tree[men] = {}
    for lei, majors in cls.items():
        names = [n for _c, n in majors]
        tree[men][lei] = names
        for n in names:
            major2[n] = [men, lei]

payload = {"men": men_order, "tree": tree, "major2": major2}
out = ROOT / "data_catalog.js"
out.write_text(
    "/* 教育部《普通高等学校本科专业目录(2026年)》三级结构: 门类 -> 专业类 -> 专业 */\n"
    "window.CAT2026=" + json.dumps(payload, ensure_ascii=False) + ";\n",
    encoding="utf-8")
n_maj = sum(len(v) for m in tree.values() for v in m.values())
print("已生成", out, f"({out.stat().st_size/1024:.1f} KB)")
print("  门类", len(tree), " 专业类", sum(len(v) for v in tree.values()), " 专业", n_maj)
