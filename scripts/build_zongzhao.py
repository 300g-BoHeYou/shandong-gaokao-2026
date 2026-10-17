# -*- coding: utf-8 -*-
"""生成 data_zongzhao.js: 2026 山东省本科综合评价招生(综招) 19 所高校数据。

数据来源: scripts/zz_seed.py (省内试点 10 所) + scripts/zz_overseas.py (省外 9 所)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from zz_seed import PILOT  # noqa: E402

try:
    from zz_overseas import OVERSEAS  # noqa: E402
except Exception:
    OVERSEAS = []


def events_of(sch):
    """从 examDate 解析校测事件: [{d:"06-14", label:"笔试", slot:"上午"}]"""
    if sch.get("events"):
        return sch["events"]
    s = sch.get("examDate") or ""
    if not re.search(r"\d{1,2}月\d{1,2}日", s):
        return []
    out = []
    # "6月14日（笔试）、6月16日（面试）" / "6月13日（机试）、6月15日（面试）"
    for m in re.finditer(r"(\d{1,2})月(\d{1,2})日\s*(?:[（(]([^）)]*)[）)])?", s):
        mo, dd, label = int(m.group(1)), int(m.group(2)), (m.group(3) or "").strip()
        slot = ""
        tail = s[m.end():m.end() + 6]
        if "上午" in tail:
            slot = "上午"
        elif "下午" in tail:
            slot = "下午"
        out.append({"d": f"{mo:02d}-{dd:02d}", "md": f"{mo}月{dd}日", "label": label or "校测", "slot": slot})
    # 区间 "6月13—14日"
    m = re.search(r"(\d{1,2})月(\d{1,2})[—\-–](\d{1,2})日", s)
    if m and len(out) <= 1:
        mo, a, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        out = [{"d": f"{mo:02d}-{x:02d}", "md": f"{mo}月{x}日", "label": "面试", "slot": ""}
               for x in range(a, b + 1)]
    seen, uniq = set(), []
    for e in out:
        if e["d"] in seen:
            continue
        seen.add(e["d"])
        uniq.append(e)
    return uniq


def clean(o):
    return {k: v for k, v in o.items() if v not in (None, "", [], {}) or k == "events"}


schools = []
for s in PILOT + OVERSEAS:
    d = dict(s)
    d["events"] = events_of(s) or []
    d["area"] = s.get("area") or ("省外" if s.get("overseas") else "省内")
    d["batch"] = s.get("batch") or ("山东提前批·综合评价招生试点" if not s.get("overseas")
                                    else "省外高校综招（各自报名系统）")
    schools.append(clean(d))
    schools[-1]["events"] = d["events"]

# 统计
total = sum(s.get("plan") or 0 for s in schools)
pilot = [s for s in schools if s["area"] == "省内"]
overseas = [s for s in schools if s["area"] == "省外"]
meta = {
    "year": 2026, "province": "山东", "updated": "2026-10",
    "totalPlan": total, "count": len(schools),
    "pilotCount": len(pilot), "overseasCount": len(overseas),
    "pilotPlan": sum(s.get("plan") or 0 for s in pilot),
    "note": "山东省2026年本科（普通类）综合评价招生：省厅试点10所（提前批，合计1970人）+ 省外自主综招9所。"
            "校测时间冲突时，报名系统内只能确认1所学校的测试；提前批也只能填报1所。",
    "policy": "鲁教学函〔2026〕13号《山东省教育厅关于做好2026年普通本科高校综合评价招生试点工作的通知》",
}
out = {"meta": meta, "schools": schools}

dest = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data_zongzhao.js"
js = ("/* 2026 山东省本科综合评价招生（综招）数据 —— 由 scripts/build_zongzhao.py 生成\n"
      "   省内试点 10 所 + 省外自主综招 9 所；校测时间为重点，来源见各校 url 字段 */\n"
      "window.ZZ2026=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")
dest.write_text(js, encoding="utf-8")

print(f"已生成 {dest.name}: {len(schools)} 所（省内 {len(pilot)} / 省外 {len(overseas)}），"
      f"计划合计 {total} 人，文件 {len(js)/1024:.1f} KB")
for s in schools:
    ev = "、".join(f"{e['md']}{e['label']}{('('+e['slot']+')') if e['slot'] else ''}" for e in s["events"]) or "待查证"
    print(f"  {s['name']:<16} {s['area']}  计划 {str(s.get('plan') or '待查证'):>5}  校测: {ev}")
