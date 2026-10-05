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
_main = ROOT / "强基查证清单.xlsx"
_split = ROOT / "强基查证清单_split.xlsx"
XLSX = _main if _main.exists() else _split
if len(sys.argv) > 2:
    XLSX = Path(sys.argv[2])
OLD_JS = ROOT / "data_qiangji.js"
OUT_JS = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data_qiangji.js"
SOURCES_P = ROOT / "qj_cache" / "sources.json"
if SOURCES_P.exists():
    SOURCES = json.loads(SOURCES_P.read_text(encoding="utf-8"))
    CODES = {k: {"code": v.get("code", "")} for k, v in SOURCES.items()}
    _JZLINKS = {k: v.get("jzLink", "") for k, v in SOURCES.items()}
else:
    CODES = json.loads((ROOT / "qj_cache" / "chsi_index.json").read_text(encoding="utf-8"))
    _JZLINKS = {}
JZ_LINKS = json.loads((ROOT / "qj_cache" / "jz_index.json").read_text(encoding="utf-8")) if (ROOT / "qj_cache" / "jz_index.json").exists() else {}

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
SPLIT_MODE = "包含专业" in s2.columns


def clean(v):
    s = str(v).strip()
    return "" if s.lower() in ("nan", "none") else s


def pick_jz_link(name):
    if _JZLINKS.get(name):
        return _JZLINKS[name]
    for g in JZ_LINKS.get(name, {}).get("fetched", []):
        u = g.get("url", "")
        if g.get("len", 0) > 4000 and "weixin" not in u and "chsi" not in u and "cyscc" not in u:
            return u
    return ""


ST = {"上榜": "ranked", "未上榜": "unranked", "特色专业": "special", "未发布": "notpub",
      "该校未收录软科": "nosc"}


def item_of(mr):
    """拆分表: 一行=一个专业"""
    st = ST.get(clean(mr.get("软科状态", "")), "notpub")
    return {
        "n": clean(mr.get("包含专业", "")),
        "rk": int(mr["软科排名"]) if clean(mr.get("软科排名", "")) else None,
        "st": st,
        "cnt": 0,
        "inList": st == "special",
        "s": int(mr["对应普通批最低分"]) if clean(mr.get("对应普通批最低分", "")) else None,
        "r": int(mr["对应普通批最低位次"]) if clean(mr.get("对应普通批最低位次", "")) else None,
        "ref": clean(mr.get("参考志愿类", "")),
        "kind": clean(mr.get("参考口径", "")),
        "warn": clean(mr.get("校验", "")),
        "fix": clean(mr.get("修正", "")),
    }


schools = []
for _, r in s1.iterrows():
    name = clean(r["院校名称"])
    code = CODES.get(name, {}).get("code", "")
    rows = s2[s2["院校名称"] == name]
    majors, order = {}, []
    for _, mr in rows.iterrows():
        cat = clean(mr.get("强基专业类名称", ""))
        if cat not in majors:
            majors[cat] = {"cat": cat, "subj": clean(mr.get("考查科目", "")),
                           "note": clean(mr.get("备注（括号内方向）", mr.get("备注", ""))), "items": []}
            order.append(cat)
        if SPLIT_MODE:
            majors[cat]["items"].append(item_of(mr))
        else:
            inc = clean(mr.get("包含专业（顿号分隔）", ""))
            rkMap = {x["n"]: x for x in old_rk.get((name, cat), [])}
            for p in [x for x in inc.split("、") if x.strip()]:
                it = {"n": p, "rk": None, "st": "notpub", "cnt": 0, "inList": False,
                      "s": int(mr["对应普通批最低分"]) if clean(mr.get("对应普通批最低分", "")) else None,
                      "r": int(mr["对应普通批最低位次"]) if clean(mr.get("对应普通批最低位次", "")) else None,
                      "ref": clean(mr.get("参考志愿类", "")), "kind": "", "warn": "", "fix": ""}
                if p in rkMap:
                    it.update({k: rkMap[p].get(k) for k in ("rk", "st", "cnt", "inList")})
                majors[cat]["items"].append(it)
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
        "majors": [majors[c] for c in order],
    })

payload = {"year": 2026, "schools": schools}
OUT_JS.write_text(
    "/* 2026 强基计划数据: 校考/入围等字段取自各校官方简章(阳光高考报名平台/学校本科招生网); "
    "每个专业类下的专业逐条列出, 各自带软科2026排名与对应普通批参考分/位次 */\n"
    "window.QJ2026=" + json.dumps(payload, ensure_ascii=False) + ";\n",
    encoding="utf-8")

print("已生成", OUT_JS)
print("  院校", len(schools), "专业类", sum(len(s["majors"]) for s in schools),
      " 专业条数", sum(len(m["items"]) for s in schools for m in s["majors"]))
print("  有官方链接", sum(1 for s in schools if s["link"]), " 有学校简章直链", sum(1 for s in schools if s["jzLink"]))
print("  有入围比例", sum(1 for s in schools if s["ratio"]), " 有校考时间", sum(1 for s in schools if s["examTime"]),
      " 有破格政策", sum(1 for s in schools if s["brk"]))
print("  拆分模式:", SPLIT_MODE)
