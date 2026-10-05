# -*- coding: utf-8 -*-
"""查 南大/西交/浙大/厦大 的考核时间原文"""
import json
import re
from pathlib import Path

C = json.loads((Path(__file__).resolve().parent.parent / "qj_cache" / "corpus.json").read_text(encoding="utf-8"))
for n in ["南京大学", "西安交通大学", "浙江大学", "厦门大学", "武汉大学", "中山大学", "大连理工大学"]:
    t = re.sub(r"\s+", "", C[n]["text"])
    print("=" * 70)
    print(n)
    for m in re.finditer(r"[^。；]{0,60}(?:考核时间|测试时间|初试|复试|考核安排|学校考核)[^。；]{0,110}", t):
        seg = m.group(0)
        if re.search(r"[0-9]{1,2}月", seg):
            print("  -", seg[:190])
