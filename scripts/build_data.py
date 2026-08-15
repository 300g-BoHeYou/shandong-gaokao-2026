# -*- coding: utf-8 -*-
"""
构建 2026 山东志愿参考数据 (投档表 + 软科排名 + 一分一段) -> JS 数据文件。

输出(仓库根目录, GitHub Pages 直接服务):
  data_ruanke.js   软科 2026 专业排名 (原始树 + 派生索引)
  data_toudang.js  2026 投档表(第一次投档) 每行志愿类数据
  data_fen.js      一分一段表(分数->位次)
"""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT   # GitHub Pages 从仓库根目录服务, 站点文件输出到根目录
OUT.mkdir(exist_ok=True)

XLSX = ROOT / "2026山东高考第一批次投档.xlsx"
RK_JSON = ROOT / "软科中国大学专业排名_2026.json"

# ---------------------------------------------------------------- 1. 软科
with open(RK_JSON, encoding="utf-8") as f:
    ruanke = json.load(f)

rk_major = {}      # majorKey("code name") -> {schoolName: rank}
rk_meta = {}       # majorKey -> {men, lei, name, count}
lei2major = {}     # 专业类名 -> [majorKey,...]
men_order = []     # 门类顺序
lei_order = []     # 专业类顺序(去重)
for men, cls in ruanke.items():
    if men not in men_order:
        men_order.append(men)
    for lei, majors in cls.items():
        if lei not in lei_order:
            lei_order.append(lei)
        lei2major.setdefault(lei, [])
        for code_name, ranks in majors.items():
            if " " in code_name:
                code, name = code_name.split(" ", 1)
            else:
                code, name = "", code_name
            key = code_name
            rk_major[key] = dict(ranks)
            rk_meta[key] = {"men": men, "lei": lei, "name": name, "count": len(ranks)}
            lei2major[lei].append(key)

# 专业名去重检查(同名不同码)
name2keys = {}
for key, meta in rk_meta.items():
    name2keys.setdefault(meta["name"], []).append(key)
dup_names = {n: ks for n, ks in name2keys.items() if len(ks) > 1}
print("软科专业总数:", len(rk_major), " 专业名重复:", len(dup_names))
for n, ks in list(dup_names.items())[:10]:
    print("  同名:", n, ks)

# 特色专业: 软科对开设<4所学校的专业只发布开设学校名单、不计算排名。
# 爬虫对这类专业填了占位排名 1 (所有学校均为 1)。
special_keys = []
for key, ranks in rk_major.items():
    vals = set(ranks.values())
    if ranks and vals == {1}:
        special_keys.append(key)
print("特色专业(软科不排名, 仅名单)数量:", len(special_keys))
print("特色专业点数:", sum(len(rk_major[k]) for k in special_keys))

# 本科专业目录(2026版)对照: 用于区分"目录内但软科未发布"与"非目录专业"
catalog_json = ROOT / "scripts" / "catalog_tree.json"
cat_names = set()
cat_lei_names = set()
if catalog_json.exists():
    with open(catalog_json, encoding="utf-8") as f:
        cat = json.load(f)
    for cls in cat["tree"].values():
        for lei, majors in cls.items():
            cat_lei_names.add(lei)
            for _code, name in majors:
                cat_names.add(name)
else:
    print("警告: scripts/catalog_tree.json 不存在, 跳过目录对照")
cat_names |= {meta["name"] for meta in rk_meta.values()}  # 并上软科名(保险)
print("目录专业名集合(2026版):", len(cat_names))

rk_schools = {s for m in rk_major.values() for s in m}
print("软科学校数:", len(rk_schools))

# ---------------------------------------------------------------- 2. 投档表
df = pd.read_excel(XLSX, sheet_name="第一次投档表", dtype=str)
print("\n投档表行数:", len(df))


def parse_name(name):
    m = re.match(r"^([0-9A-Za-z]{1,4})\s+(.*)$", str(name).strip())
    if m:
        return m.group(1), m.group(2).strip()
    return "", str(name).strip()


def split_core_note(full):
    """按第一个括号拆分: (核心名, 括号备注或''). 对括号未闭合的截断行作防御处理。"""
    m = re.search(r"[（(]", full)
    if m:
        note = full[m.start() + 1:]
        # 去掉可能的结尾括号; 嵌套括号 (如 A)(B)) 保留原样由前端再拆分
        note = note.rstrip(")）")
        return full[: m.start()].strip(), note.strip()
    return full, ""


school_cache = {}


def school_parts(s):
    """'A003清华大学' -> ('A003','清华大学')"""
    m = re.match(r"^([0-9A-Za-z]+)(.*)$", str(s).strip())
    if m and m.group(1) and m.group(2):
        return m.group(1), m.group(2).strip()
    return "", str(s).strip()


def normalize_school(name):
    return re.sub(r"\s+", "", name)


# 软科学校名归一化: 去空白 + 全角括号->半角
rk_school_norm = {}
for s in rk_schools:
    key = normalize_school(s).replace("（", "(").replace("）", ")")
    rk_school_norm.setdefault(key, s)

# 校区/分校后缀回退规则
SUFFIX_PATTERNS = [
    r"克拉玛依校区$",
    r"秦皇岛分校$",
    r"威海分校$",
    r"青岛校区$",
    r"济南校区$",
    r"医学部$",
    r"医学院$",
    r"[（(][^（()）]*校区[）)]$",
    r"[（(][^（()）]*分校[）)]$",
    r"[（(][^（()）]*[）)]$",
]


def canonical_school(td_name):
    """投档表院校名 -> 软科院校名(或 '')"""
    if td_name in school_cache:
        return school_cache[td_name]
    norm = normalize_school(td_name).replace("（", "(").replace("）", ")")
    if norm in rk_school_norm:
        school_cache[td_name] = rk_school_norm[norm]
        return rk_school_norm[norm]
    # 迭代剥后缀
    cur = norm
    for _ in range(4):
        nxt = cur
        for pat in SUFFIX_PATTERNS:
            nxt = re.sub(pat, "", nxt)
            if nxt != cur and nxt in rk_school_norm:
                school_cache[td_name] = rk_school_norm[nxt]
                return rk_school_norm[nxt]
            if nxt != cur and normalize_school(nxt) in rk_school_norm:
                school_cache[td_name] = rk_school_norm[normalize_school(nxt)]
                return rk_school_norm[normalize_school(nxt)]
        if nxt == cur:
            break
        cur = nxt
    school_cache[td_name] = ""
    return ""


# ---------------------------------------------------------------- 3. 组装投档行
# 试验班查证结果: key="院校代码|志愿类全名|最低位次" -> {mode:'list'|'renxuan'|'notfound', ...}
syb_data = {}
syb_json = ROOT / "scripts" / "syb_data.json"
if syb_json.exists():
    with open(syb_json, encoding="utf-8") as f:
        syb_data = json.load(f)
    print("试验班查证数据条目:", len(syb_data))

td_rows = []          # [sc, school, core, note, xk, score, rank, type, syb]
td_schools = set()
type_map = {}
xk_map = {}
unmatched_schools = {}
truncated_rows = []   # 名称截断(括号未闭合)的行
for _, r in df.iterrows():
    code, full = parse_name(r["专业代号及名称"])
    if ("(" in full or "（" in full) and not re.search(r"[)）]$", full):
        truncated_rows.append((full, str(r["院校代号及名称"])))
    core, note = split_core_note(full)
    sc, school = school_parts(r["院校代号及名称"])
    xk = str(r["选考科目要求"]).strip()
    try:
        score = int(float(r["最低分"]))
    except (TypeError, ValueError):
        score = None
    try:
        rank = int(float(r["最低位次"]))
    except (TypeError, ValueError):
        rank = None
    typ = str(r["专项计划/中外合作"]).strip() if pd.notna(r["专项计划/中外合作"]) else "普通"
    syb_key = f"{sc}|{full}|{rank}"
    syb = syb_data.get(syb_key) if syb_data else None
    td_rows.append([sc, school, core, note, xk, score, rank, typ, syb])
    td_schools.add(school)
    type_map[typ] = type_map.get(typ, 0) + 1
    xk_map[xk] = xk_map.get(xk, 0) + 1
    rk = canonical_school(school)
    if not rk:
        unmatched_schools.setdefault(school, 0)
        unmatched_schools[school] += 1

print("投档行数:", len(td_rows))
if truncated_rows:
    print("!! 警告: 名称截断(括号未闭合)的行数:", len(truncated_rows))
    for full, sch in truncated_rows:
        print("   ", sch, "|", full)
print("招生类型分布:", type_map)
print("\n选科要求种类:", len(xk_map))
print("未匹配到软科的院校数:", len(unmatched_schools), " 行数:", sum(unmatched_schools.values()))
print("未匹配院校(前40):")
for s, c in sorted(unmatched_schools.items(), key=lambda x: -x[1])[:40]:
    print("  ", s, c)

# ---------------------------------------------------------------- 4. 一分一段
fen_df = pd.read_excel(XLSX, sheet_name="一分一段表", dtype=str)
fen_rows = []
for _, r in fen_df.iterrows():
    try:
        fen_rows.append([int(float(r["分数"])), int(float(r["名次"]))])
    except (TypeError, ValueError):
        pass
fen_rows.sort(key=lambda x: -x[0])
print("\n一分一段行数:", len(fen_rows), " 分数范围:", fen_rows[0][0], "-", fen_rows[-1][0])

# ---------------------------------------------------------------- 5. 大类->包含专业(目录口径)
# 投档表核心名集合
cores = [r[2] for r in td_rows]
core_set = set(cores)
lei_names = [c for c in core_set if c.endswith("类")]
matched_lei = [c for c in lei_names if c in lei2major]
unmatched_lei = sorted(set(lei_names) - set(lei2major))
print("\n'xx类'核心名:", len(lei_names), " 匹配软科专业类:", len(matched_lei), " 未匹配:", unmatched_lei)

# 具体专业名(不在类表里的核心名, 且属于软科具体专业)
specific_in_rk = sorted(c for c in core_set - set(lei2major) if c in name2keys)
print("具体专业名命中软科:", len(specific_in_rk))

# 意向专业全集: 软科专业 + 投档表非类非试验班的核心名
extra_cores = sorted(
    c for c in core_set - set(lei2major) - set(name2keys)
    if not re.search(r"试验班|实验班|试点班", c)
)
print("投档表特有核心名(拟加入意向专业):", len(extra_cores))

# 检查: 类名含'类'但软科把它当具体专业的情况(如'法学类'不存在?)
# 意向专业列表: [ {n:名称, m:门类, l:专业类} ] 按门类分组
intent_list = []
for key, meta in sorted(rk_meta.items(), key=lambda kv: (men_order.index(kv[1]["men"]) if kv[1]["men"] in men_order else 99, lei_order.index(kv[1]["lei"]) if kv[1]["lei"] in lei_order else 99, kv[1]["name"])):
    intent_list.append({"n": meta["name"], "m": meta["men"], "l": meta["lei"]})
for c in extra_cores:
    intent_list.append({"n": c, "m": "其他", "l": "未分类"})
print("意向专业总数:", len(intent_list))

# 试验班/缺少具体专业的志愿类统计 (供核对)
TEST_BAN = re.compile(r"试验班|实验班|试点班")
shiyan_rows = [r for r in td_rows if TEST_BAN.search(r[2])]
from collections import Counter
shiyan_names = Counter(r[2] for r in shiyan_rows)
print("\n[统计] 缺少具体专业的志愿类(试验班/实验班/试点班): 行数 =", len(shiyan_rows))
print("       去重核心名数 =", len(shiyan_names), " 分布:", dict(shiyan_names.most_common()))

# ---------------------------------------------------------------- 6. 写 JS
def js_str(s):
    return json.dumps(s, ensure_ascii=False)


with open(OUT / "data_ruanke.js", "w", encoding="utf-8") as f:
    f.write("/* 软科中国大学专业排名 2026 (仅前50%院校上榜) */\n")
    f.write("window.RK2026=" + js_str(ruanke) + ";\n")
    f.write("/* 派生: majorKey -> {men,lei,name,count} */\n")
    f.write("window.RK_META=" + js_str(rk_meta) + ";\n")
    f.write("/* 专业类 -> [majorKey,...] */\n")
    f.write("window.RK_LEI2MAJOR=" + js_str(lei2major) + ";\n")
    f.write("/* 门类/专业类顺序 */\n")
    f.write("window.RK_MEN_ORDER=" + js_str(men_order) + ";\n")
    f.write("window.RK_LEI_ORDER=" + js_str(lei_order) + ";\n")
    f.write("/* 特色专业(软科只发布开设名单, 不计算排名) */\n")
    f.write("window.RK_SPECIAL=" + js_str({k: True for k in special_keys}) + ";\n")
    f.write("/* 本科专业目录(2026版)专业名集合, 用于区分'目录内未排名'与'非目录专业' */\n")
    f.write("window.CAT_NAMES=" + js_str(sorted(cat_names)) + ";\n")

with open(OUT / "data_toudang.js", "w", encoding="utf-8") as f:
    f.write("/* 2026山东高考第一次投档表 志愿类数据 */\n")
    f.write("/* [院校代号,院校名,专业核心名,括号备注,选科要求,最低分,最低位次,招生类型,试验班查证] */\n")
    f.write("/* 试验班查证: null=未公开; {mode:'list',majors:[专业名]} ; {mode:'renxuan',dir:'理科任选'} ; {mode:'notfound'} */\n")
    f.write("window.TD2026=" + js_str(td_rows) + ";\n")
    # 院校名 -> 软科院校名 映射
    td_school_rk = {s: canonical_school(s) for s in td_schools}
    f.write("/* 投档表院校名 -> 软科院校名(空串=软科未收录) */\n")
    f.write("window.TD_SCHOOL_RK=" + js_str(td_school_rk) + ";\n")

with open(OUT / "data_fen.js", "w", encoding="utf-8") as f:
    f.write("/* 一分一段表 [分数,位次] 降序 */\n")
    f.write("window.FEN2026=" + js_str(fen_rows) + ";\n")

print("\n已写出: data_ruanke.js, data_toudang.js, data_fen.js (仓库根目录)")
import os
for fn in ["data_ruanke.js", "data_toudang.js", "data_fen.js"]:
    p = OUT / fn
    print(f"  {fn}: {p.stat().st_size/1024:.0f} KB")
