# -*- coding: utf-8 -*-
"""核查: 厦大数学类 600 分来源; 上交试验班查证是否覆盖数学等专业。"""
import json
import re

import pandas as pd

td = pd.read_excel("2026山东高考第一批次投档.xlsx", sheet_name="第一次投档表", dtype=str)


def sp(s):
    m = re.match(r"^([0-9A-Za-z]+)(.*)$", str(s).strip())
    return m.group(2).strip() if m else str(s).strip()


sub = td[td["院校代号及名称"].str.contains("厦门大学", na=False)]
print("== 含'厦门大学'的院校名 ==")
print(sorted(set(sp(x) for x in sub["院校代号及名称"])))
print("\n== 厦门大学 数学相关志愿类 ==")
for _, r in sub.iterrows():
    if "数学" in str(r["专业代号及名称"]):
        print("  ", r["专业代号及名称"], "|", sp(r["院校代号及名称"]), "|",
              r["最低分"], r["最低位次"], "|", r["专项计划/中外合作"])

sj = td[td["院校代号及名称"].str.contains("上海交通大学", na=False)]
print("\n== 上海交通大学 志愿类(前14) ==")
for _, r in sj.head(14).iterrows():
    print("  ", r["专业代号及名称"], "|", sp(r["院校代号及名称"]), "|", r["最低分"], r["最低位次"])

mc = json.load(open("scripts/manual_check.json", encoding="utf-8"))
syb = mc.get("试验班", {})
hits = [(k, v) for k, v in syb.items() if k.startswith("A248") and v.get("mode") == "list"]
print("\n上交(A248)已查证试验班:", len(hits), "/ 总条目", len(syb))
for k, v in hits[:10]:
    print("  ", k, "→", "、".join(v["majors"])[:90])
