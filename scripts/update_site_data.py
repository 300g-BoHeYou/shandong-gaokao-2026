# -*- coding: utf-8 -*-
"""由 强基查证清单_官方核对.xlsx + 既有 data_qiangji.js 生成新的 data_qiangji.js。

- Sheet1 官方字段(入围比例/入围方式/入围成绩计算/校考时间/校考形式/竞赛破格/报名时间/备注)
- Sheet2 专业类行(包含专业/考查科目/备注/对应普通批参考分与位次/参考志愿类)
- 每校官方链接: 阳光高考强基报名平台(权威稳定) + 学校官网简章(有则附上)
- 软科排名信息沿用既有 JS 中的 incRk
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
XLSX = ROOT / "强基查证清单_官方核对.xlsx"
OLD_JS = ROOT / "data_qiangji.js"
OUT_JS = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data_qiangji.js"
CODES = json.loads((ROOT / "qj_cache" / "chsi_index.json").read_text(encoding="utf-8"))
JZ_LINKS = json.loads((ROOT / "qj_cache" / "jz_index.json").read_text(encoding="utf-8"))

# 旧 JS 中的软科排名信息
old = OLD_JS.read_text(encoding="utf-8")
m = re.search(r"window\.QJ2026=(\{.*\});", old, re.S)
OLD = json.loads(m.group(1))
old_rk = {}
for s in OLD["schools"]:
    for mj in s["majors"]:
        old_rk[(s["name"], mj["cat"])] = mj.get("incRk", [])

s1 = pd.read_excel(XLSX, sheet_name="院校信息").fillna("")
s2 = pd.read_excel(XLSX, sheet_name="专业信息").fillna("")


def clean(v):
    s = str(v).strip()
    return "" if s.lower() in ("nan", "none") else s


def pick_jz_link(name):
    for g in JZ_LINKS.get(name, {}).get("fetched", []):
        u = g.get("url", "")
        if g.get("len", 0) > 4000 and "weixin" not in u and "chsi" not in u and "cyscc" not in u:
            return u
    return ""


schools = []
for _, r in s1.iterrows():
    name = clean(r["院校名称"])
    code = CODES.get(name, {}).get("code", "")
    rows = s2[s2["院校名称"] == name]
    majors = []
    for _, mr in rows.iterrows():
        cat = clean(mr.get("强基专业类名称", ""))
        inc = clean(mr.get("包含专业（顿号分隔）", ""))
        majors.append({
            "cat": cat,
            "inc": inc,
            "incRk": old_rk.get((name, cat), []),
            "subj": clean(mr.get("考查科目", "")),
            "s": int(mr["对应普通批最低分"]) if clean(mr.get("对应普通批最低分", "")) else None,
            "r": int(mr["对应普通批最低位次"]) if clean(mr.get("对应普通批最低位次", "")) else None,
            "ref": clean(mr.get("参考志愿类", "")),
            "note": clean(mr.get("备注（括号内方向）", "")),
        })
    schools.append({
        "name": name,
        "mode": clean(r.get("校考模式", "")),
        "examTime": clean(r.get("校考时间", "")),
        "ratio": clean(r.get("入围比例", "")),
        "entry": clean(r.get("入围方式", "")),
        "entryScore": clean(r.get("入围成绩计算", "")),
        "form": clean(r.get("校考形式", "")),
        "brk": clean(r.get("竞赛破格政策", "")),
        "signup": clean(r.get("报名时间", "")),
        "note": clean(r.get("备注", "")),
        "link": f"https://bm.chsi.com.cn/jcxkzs/sch/{code}" if code else "https://gaokao.chsi.com.cn/gkzt/jcxkzs",
        "jzLink": pick_jz_link(name),
        "majors": majors,
    })

payload = {"year": 2026, "schools": schools}
OUT_JS.write_text(
    "/* 2026 强基计划数据: 校考/入围等字段取自各校官方简章(阳光高考报名平台/学校本科招生网), "
    "专业类含软科2026排名; 标注「待查证」的字段以院校当年简章为准 */\n"
    "window.QJ2026=" + json.dumps(payload, ensure_ascii=False) + ";\n",
    encoding="utf-8")

print("已生成", OUT_JS)
print("  院校", len(schools), "专业类行", sum(len(s["majors"]) for s in schools))
print("  有官方链接", sum(1 for s in schools if s["link"]), " 有学校简章直链", sum(1 for s in schools if s["jzLink"]))
print("  有入围比例", sum(1 for s in schools if s["ratio"]), " 有校考时间", sum(1 for s in schools if s["examTime"]),
      " 有破格政策", sum(1 for s in schools if s["brk"]))
