# -*- coding: utf-8 -*-
"""生成 data_zongzhao.js: 2026 山东省本科综合评价招生(综招) 19 所高校数据。

要点:
  - 招生专业(类) 一律解析到《本科专业目录(2026)》的具体专业; 是「类」的按目录展开, 并附该校软科排名
  - 记录每校实际层级(是否有专业组 / 是否有「类」展开), 前端据此决定表格列数
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from zz_seed import PILOT          # noqa: E402
from zz_overseas import OVERSEAS   # noqa: E402


# ---------- 读取 目录 / 软科 ----------
def _load_json_global(path, var):
    s = path.read_text(encoding="utf-8")
    i = s.index(var + "=")
    i = s.index("{", i)
    obj, _ = json.JSONDecoder().raw_decode(s[i:])
    return obj


CAT = _load_json_global(ROOT / "data_catalog.js", "CAT2026")
RK = _load_json_global(ROOT / "data_ruanke.js", "RK2026")
TD = _load_json_global(ROOT / "data_toudang.js", "TD2026")

LEI2MAJORS, MAJ2, RK_NAME, RK_SCHOOLS = {}, {}, {}, set()
for men, leis in CAT.get("tree", {}).items():
    for lei, majs in leis.items():
        LEI2MAJORS[lei] = list(majs)
        for m in majs:
            MAJ2[m] = (men, lei)
for men, leis in RK.items():
    for lei, majors in leis.items():
        for key, d in majors.items():
            nm = key.split(" ", 1)[1].strip() if " " in key else key.strip()
            RK_NAME.setdefault(nm, {}).update(d)
            RK_SCHOOLS.update(d.keys())

# ---------- 一批次投档表: 该校实际开设(直接招生 ∪ 大类有效专业) ----------
# TD 行: [院校代号, 院校名, 专业核心名, 括号备注, 选科, 最低分, 最低位次, 招生类型, 试验班查证, 大类有效专业]
OFFER = {}          # 学校 -> set(专业名)
LEI_EFF = {}        # (学校, 类名) -> set(专业名)  取自投档表「大类有效专业」
for _r in TD:
    if not isinstance(_r, list) or len(_r) < 10:
        continue
    _sc, _core, _eff = _r[1], str(_r[2] or ""), _r[9]
    _st = OFFER.setdefault(_sc, set())
    if not (_core.endswith("类") or _core.endswith("试验班") or _core.endswith("班")):
        _st.add(_core)
    if isinstance(_eff, list):
        _names = {(x.split(" ", 1)[1].strip() if " " in x else x.strip()) for x in _eff}
        _names.discard("")
        _st |= _names
        if _core.endswith("类"):
            LEI_EFF.setdefault((_sc, _core), set()).update(_names)


def offer_of(school):
    """该校实际开设专业 = 一批次直接招生 ∪ 投档大类有效专业 ∪ 软科上榜"""
    s = set(OFFER.get(school, set()))
    for nm, d in RK_NAME.items():
        if school in d or school.replace("（", "(").replace("）", ")") in d:
            s.add(nm)
    return s

ALIAS = {
    "中国石油大学（华东）": ["中国石油大学(华东)", "中国石油大学（华东）"],
    "哈尔滨工业大学（威海）": ["哈尔滨工业大学(威海)", "哈尔滨工业大学（威海）", "哈尔滨工业大学"],
    "香港中文大学（深圳）": ["香港中文大学(深圳)", "香港中文大学（深圳）"],
    "山东大学": ["山东大学"],
    "中国海洋大学": ["中国海洋大学"],
}


def rk_of(school, major):
    """返回 {n, st, rk, cnt}: st = ranked / unranked / special / notpub / nodir / nosc"""
    d = RK_NAME.get(major)
    if d is None:
        return {"n": major, "st": "notpub" if major in MAJ2 else "nodir", "cnt": 0}
    cnt = len(d)
    st = "special" if cnt < 4 else None
    rank = None
    for nm in ALIAS.get(school, [school]):
        if nm in d:
            rank = d[nm]
            break
    if school not in RK_SCHOOLS:
        return {"n": major, "st": "nosc", "cnt": cnt}
    if rank is None:
        return {"n": major, "st": "unranked", "cnt": cnt}
    return {"n": major, "st": st or "ranked", "rk": rank, "cnt": cnt}


def strip_parens(n):
    s = str(n or "")
    for _ in range(3):
        s2 = re.sub(r"[（(][^（()）]*[)）]\s*$", "", s)
        if s2 == s:
            break
        s = s2
    return s.strip()


# 简章未在括号内列明、但官方另有说明的具体专业(个别院校)
LEI_OVERRIDE = {
    ("山东师范大学", "外国语言文学类"): ["俄语", "日语", "朝鲜语"],   # 简章注: 含俄语(师范)、日语(师范)、朝鲜语
}


def paren_majors(n):
    """简章名括号内若以「、」列出的都是目录专业, 则以它为准(如 山财 经济学类（经济学、资源与环境经济学）)"""
    m = re.search(r"[（(]([^（()）]*)[)）]\s*$", str(n or ""))
    if not m:
        return []
    inner = m.group(1)
    if "、" not in inner or "含" in inner or "双学位" in inner:
        return []
    toks = [t.strip() for t in inner.split("、") if t.strip()]
    if len(toks) >= 2 and all(t in MAJ2 for t in toks):
        return toks
    return []


def norm_entry(school, n):
    """把简章里的招生专业(类)解析为 {n, cls, subs[], kind}
    「类」按该校实际开设筛减, 优先级:
      ① 简章括号内列明的专业 → ② 简章注明的特例 → ③ 一批次同名大类的「大类有效专业」
      → ④ (目录类内专业 ∩ 该校开设[投档直接招生∪软科上榜])"""
    base = strip_parens(n)
    if base in LEI2MAJORS:
        offer = offer_of(school)
        cand = paren_majors(n)
        if not cand:
            cand = LEI_OVERRIDE.get((school, base), [])
        if not cand:
            eff = LEI_EFF.get((school, base))
            if eff:
                cand = [m for m in LEI2MAJORS[base] if m in eff]
        else:
            cand = [m for m in cand if m in MAJ2]
        if not cand:
            cand = [m for m in LEI2MAJORS[base] if m in offer]
        if not cand:
            return {"n": n, "cls": base, "kind": "lei", "subs": [], "todo": True}
        subs = [rk_of(school, m) for m in cand]
        return {"n": n, "cls": base, "kind": "lei", "subs": subs}
    if base in MAJ2:
        return {"n": n, "cls": base, "kind": "major", "subs": [rk_of(school, base)]}
    return {"n": n, "cls": base, "kind": "other", "subs": []}


def events_of(sch):
    if sch.get("events"):
        return sch["events"]
    s = sch.get("examDate") or ""
    if not re.search(r"\d{1,2}月\d{1,2}日", s):
        return []
    out = []
    for m in re.finditer(r"(\d{1,2})月(\d{1,2})日", s):
        mo, dd = int(m.group(1)), int(m.group(2))
        out.append({"d": f"{mo:02d}-{dd:02d}", "md": f"{mo}月{dd}日", "label": "校测", "slot": ""})
    return out


def clean(o):
    return {k: v for k, v in o.items() if v not in (None, "", [], {}) or k in ("events", "subs")}


schools = []
stats = {"lei": 0, "major": 0, "other": 0, "ranked": 0, "unranked": 0, "notpub": 0, "nodir": 0, "nosc": 0, "special": 0}
for s in PILOT + OVERSEAS:
    d = dict(s)
    d["events"] = events_of(s) or []
    d["area"] = s.get("area") or ("省外" if s.get("overseas") else "省内")
    d["batch"] = s.get("batch") or ("山东提前批·综合评价招生试点" if not s.get("overseas")
                                    else "省外高校综招（各自报名系统）")
    groups = []
    has_class = False
    for g in (s.get("groups") or []):
        entries = []
        for m in (g.get("majors") or []):
            e = norm_entry(s["name"], m["n"])
            e["req"] = m.get("req") or ""
            entries.append(e)
            stats[e["kind"]] = stats.get(e["kind"], 0) + 1
            if e["kind"] == "lei":
                has_class = True
            for sub in e["subs"]:
                stats[sub["st"]] = stats.get(sub["st"], 0) + 1
        groups.append({"name": g.get("name", ""), "req": g.get("req", ""), "entries": entries})
    d["groups"] = groups
    d["hasGroup"] = len(groups) > 1
    d["hasClass"] = has_class
    schools.append(clean(d))

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
    "majorNote": "招生专业(类)已解析到《本科专业目录(2026)》的具体专业；标为「类」的按目录展开，"
                 "并附该校该专业的软科2026排名（前50%上榜，<4所开设为特色专业）；实际包含专业以院校简章为准。",
}
out = {"meta": meta, "schools": schools}

dest = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data_zongzhao.js"
js = ("/* 2026 山东省本科综合评价招生（综招）数据 —— 由 scripts/build_zongzhao.py 生成\n"
      "   省内试点 10 所 + 省外自主综招 9 所；招生专业已解析到目录具体专业并附软科排名 */\n"
      "window.ZZ2026=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")
dest.write_text(js, encoding="utf-8")

print(f"已生成 {dest.name}: {len(schools)} 所（省内 {len(pilot)} / 省外 {len(overseas)}），"
      f"计划合计 {total} 人，文件 {len(js)/1024:.1f} KB")
print(f"专业条目: 类展开 {stats['lei']} / 直接专业 {stats['major']} / 未在目录 {stats['other']}")
print(f"软科状态: 上榜 {stats['ranked']} / 未上榜 {stats['unranked']} / 特色 {stats['special']} / "
      f"未发布 {stats['notpub']} / 非目录 {stats['nodir']} / 校未收录 {stats['nosc']}")
for s in schools:
    n_maj = sum(len(e["subs"]) for g in s["groups"] for e in g["entries"])
    print(f"  {s['name']:<16} 组{s['hasGroup'] and len(s['groups']) or 0} 类{s['hasClass'] and 'Y' or 'N'} "
          f"条目{sum(len(g['entries']) for g in s['groups']):>3} 具体专业{n_maj:>3}")
