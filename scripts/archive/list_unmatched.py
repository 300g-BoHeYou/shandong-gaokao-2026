# -*- coding: utf-8 -*-
"""列出全部未匹配软科的院校, 人工检查可回退项。"""
import json
import re

import pandas as pd

df = pd.read_excel("2026山东高考第一批次投档.xlsx", sheet_name="第一次投档表", dtype=str)
schools = df["院校代号及名称"].str.replace(r"^[0-9A-Za-z]+", "", regex=True).unique()

with open("软科中国大学专业排名_2026.json", encoding="utf-8") as f:
    ruanke = json.load(f)

rk_schools = {s for m in ruanke.values() for cls in m.values() for rks in cls.values() for s in rks}
norm = lambda s: re.sub(r"\s+", "", s).replace("（", "(").replace("）", ")")


def canon(td_name):
    n = norm(td_name)
    if n in {norm(s) for s in rk_schools}:
        return True
    for pat in [r"克拉玛依校区$", r"秦皇岛分校$", r"威海分校$", r"青岛校区$", r"济南校区$", r"医学部$",
                r"[（(][^（()）]*校区[）)]$", r"[（(][^（()）]*分校[）)]$", r"[（(][^（()）]*[）)]$"]:
        n2 = re.sub(pat, "", n)
        if n2 != n and n2 in {norm(s) for s in rk_schools}:
            return True
    return False


unmatched = [s for s in schools if not canon(s)]
print("未匹配院校数:", len(unmatched))
for s in sorted(unmatched):
    print(s)
