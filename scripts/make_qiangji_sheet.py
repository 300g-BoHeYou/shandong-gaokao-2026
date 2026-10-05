# -*- coding: utf-8 -*-
"""
强基计划查证清单 + 网页数据生成（按用户 2026-04 反馈修订）

规则:
  1) 校考模式只说“出分前/出分后”，不使用民间俗称
  2) 仅面试院校 考查科目 标注“无笔试”
  3) 不展示院校级分数/位次，只保留分专业参考（分/位次）
  4) 强基专业名若为本科专业目录中的“具体专业”，直接预填到包含专业；
     大类名(如 化学类)保留待查；带括号方向的按去括号后名称预填并给出提示
  5) 来源冲突时以官方为准（东南=官网新闻，专业表为图片→留空；吉林=官方简章）
  6) 已确定专业标注软科 2026 排名状态
  7) 清华按文/理试验班标注分专业参考
输出:
  强基查证清单.xlsx (Sheet1 院校信息 / Sheet2 专业信息)
  data_qiangji.js
"""
import json
import re
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
XLSX = ROOT / "2026山东高考第一批次投档.xlsx"
OUT_SHEET = ROOT / "强基查证清单.xlsx"
OUT_JS = ROOT / "data_qiangji.js"

# ============================================================
# 目录 & 软科
# ============================================================
with open(ROOT / "scripts" / "catalog_tree.json", encoding="utf-8") as f:
    cat = json.load(f)
cat_names, lei_names = set(), set()
for cls in cat["tree"].values():
    for lei, majors in cls.items():
        lei_names.add(lei)
        for _code, nm in majors:
            cat_names.add(nm)

with open(ROOT / "软科中国大学专业排名_2026.json", encoding="utf-8") as f:
    ruanke = json.load(f)
rk_major, name2keys, special_keys = {}, {}, set()
for men, cls in ruanke.items():
    for lei, majors in cls.items():
        for code_name, ranks in majors.items():
            name = code_name.split(" ", 1)[1] if " " in code_name else code_name
            rk_major[code_name] = dict(ranks)
            name2keys.setdefault(name, []).append(code_name)
            if ranks and set(ranks.values()) == {1}:
                special_keys.add(code_name)
rk_schools = {s for m in rk_major.values() for s in m}
rk_norm = {}
for s in rk_schools:
    rk_norm.setdefault(re.sub(r"\s+", "", s).replace("（", "(").replace("）", ")"), s)
SUFFIX = [r"克拉玛依校区$", r"秦皇岛分校$", r"威海分校$", r"青岛校区$", r"济南校区$",
          r"医学部$", r"医学院$", r"[（(][^（()）]*校区[）)]$", r"[（(][^（()）]*分校[）)]$",
          r"[（(][^（()）]*[）)]$"]


def canonical_school(name):
    n = re.sub(r"\s+", "", name).replace("（", "(").replace("）", ")")
    if n in rk_norm:
        return rk_norm[n]
    cur = n
    for _ in range(4):
        nxt = cur
        for pat in SUFFIX:
            n2 = re.sub(pat, "", nxt)
            if n2 != nxt and n2 in rk_norm:
                return rk_norm[n2]
        if nxt == cur:
            break
        cur = nxt
    return ""


def rank_info(school, major_name):
    """返回 {rk, st, cnt} — st: ranked/unranked/special/notpub"""
    rk_school = canonical_school(school)
    keys = name2keys.get(major_name) or []
    if not keys:
        return {"rk": None, "st": "notpub", "cnt": 0}
    key = keys[0]
    if key in special_keys:
        in_list = bool(rk_school and rk_school in rk_major[key])
        return {"rk": None, "st": "special", "cnt": len(rk_major[key]), "inList": in_list}
    if not rk_school:
        return {"rk": None, "st": "notpub", "cnt": len(rk_major[key])}
    ranks = rk_major[key]
    if rk_school in ranks:
        return {"rk": ranks[rk_school], "st": "ranked", "cnt": len(ranks)}
    return {"rk": None, "st": "unranked", "cnt": len(ranks)}


# ============================================================
# 投档表(分专业普通批参考)
# ============================================================
td = pd.read_excel(XLSX, sheet_name="第一次投档表", dtype=str)


def parse_name(name):
    m = re.match(r"^([0-9A-Za-z]{1,4})\s+(.*)$", str(name).strip())
    return (m.group(1), m.group(2).strip()) if m else ("", str(name).strip())


def split_core_note(full):
    m = re.search(r"[（(]", full)
    if m:
        return full[: m.start()].strip(), full[m.start() + 1:].rstrip(")）").strip()
    return full, ""


def school_parts(s):
    m = re.match(r"^([0-9A-Za-z]+)(.*)$", str(s).strip())
    if m and m.group(1) and m.group(2):
        return m.group(1), m.group(2).strip()
    return "", str(s).strip()


school_majors = {}   # 校 -> {志愿类核心名: (分,位次)}
for _, r in td.iterrows():
    _c, full = parse_name(r["专业代号及名称"])
    core, _n = split_core_note(full)
    _s, school = school_parts(r["院校代号及名称"])
    typ = str(r["专项计划/中外合作"]).strip() if pd.notna(r["专项计划/中外合作"]) else "普通"
    if typ != "普通":
        continue
    try:
        score, rank = int(float(r["最低分"])), int(float(r["最低位次"]))
    except (TypeError, ValueError):
        continue
    school_majors.setdefault(school, {}).setdefault(core, (score, rank))

ALIAS = {"数学类": ["数学类", "数学与应用数学"], "物理学类": ["物理学类", "物理学"],
         "化学类": ["化学类", "化学"], "生物科学类": ["生物科学类", "生物科学"],
         "历史学类": ["历史学类", "历史学"], "哲学类": ["哲学类", "哲学"],
         "力学类": ["力学类", "工程力学"], "核工程类": ["核工程类", "核工程与核技术"],
         "航空航天类": ["航空航天类", "航空航天工程"],
         "数学与应用数学": ["数学与应用数学", "数学类"], "应用物理学": ["应用物理学", "物理学"],
         "应用化学": ["应用化学", "化学"], "理论与应用力学": ["理论与应用力学", "工程力学"],
         "基础医学": ["基础医学", "临床医学类"], "基础医学（八年制）": ["基础医学", "临床医学类"],
         "汉语言文学（古文字学方向）": ["汉语言文学", "中国语言文学类"],
         "汉语言文学（古文字学）": ["汉语言文学"], "汉语言文学（古文字方向）": ["汉语言文学"],
         "中国语言文学类（古文字学方向）": ["中国语言文学类", "汉语言文学"],
         "中国少数民族语言文学（古文字学方向）": ["中国少数民族语言文学"],
         "草业科学（草类植物生物育种）": ["草业科学"], "药学（生物医药）": ["药学"],
         "测控技术与仪器（量子信息）": ["测控技术与仪器"],
         "复合材料与工程（航天材料）": ["复合材料与工程"],
         "材料科学与工程（航天材料）": ["材料科学与工程"]}


def match_major(school, cat):
    ms = school_majors.get(school) or {}
    for cand in ALIAS.get(cat, [cat]):
        if cand in ms:
            return ms[cand]
    for cand in ALIAS.get(cat, [cat]):
        for k, v in ms.items():
            if cand and (cand in k or k in cand):
                return v
    return (None, None)


# 清华: 按文/理试验班标注
TSINGHUA_LI = ["数学与应用数学", "物理学", "化学", "生物科学", "信息与计算科学",
               "数理基础科学", "化学生物学", "理论与应用力学"]
TSINGHUA_WEN = ["中国语言文学类（古文字学方向）", "历史学类", "哲学类"]


def tsinghua_ref(cat):
    ms = school_majors.get("清华大学") or {}
    if cat in TSINGHUA_LI:
        for k in ("理科试验班(理科各专业)", "理科试验班类", "理科试验班"):
            if k in ms:
                return ms[k]
    if cat in TSINGHUA_WEN:
        for k in ("文科试验班类(文科各专业)", "文科试验班类"):
            if k in ms:
                return ms[k]
    return (None, None)


def derive_included(cat):
    """规则4: 具体专业→直接预填; 带括号→去括号后判断并返回提示; 大类→待查"""
    m = re.match(r"^(.*?)[（(](.*)[)）]$", cat)
    base = m.group(1).strip() if m else cat
    raw_hint = cat if m else ""
    if base in cat_names and base not in lei_names:
        return [base], raw_hint
    return [], ""


# ============================================================
# 院校数据
# ============================================================
SCHOOLS = [
    # ---------- 出分前校考 11 所 ----------
    dict(name="复旦大学", mode="出分前", examTime="初试6月12日，复试6月22日前", form="笔试+面试+体测",
         note="初试笔试科目按专业确定；A类考生校测成绩=初试100分+复试面试50分，B类考生为面试折算150分",
         majors=[("数学与应用数学", "数学"), ("信息与计算科学", "数学、计算科学"), ("物理学", "物理"),
                 ("化学", "化学"), ("生物科学类", "数理化综合"), ("基础医学", "数理化综合"),
                 ("中国语言文学类（古文字学）", "文史哲综合"), ("历史学", "文史哲综合"), ("哲学", "文史哲综合")]),
    dict(name="上海交通大学", mode="出分前", examTime="初试6月12日", form="笔试+面试+体测",
         note="校测分笔试(初试)、综合面试(复试)、体测；笔试科目按专业组区分",
         majors=[("数学与应用数学", "数学+物理"), ("物理学", "数学+物理"), ("生物医学工程", "数学+物理"),
                 ("工程力学", "数学+物理"), ("船舶与海洋工程", "数学+物理"), ("材料科学与工程", "数学+物理"),
                 ("化学", "数学+化学"), ("生物科学", "数学+化学"), ("生物医学科学", "数学+化学")]),
    dict(name="南京大学", mode="出分前", examTime="初试6月19日左右，复试6月21日左右", form="笔试+面试+体测",
         note="2026年变化：理科类初试考“数理探究”，文科类考“阅读表达”",
         majors=[("数学与应用数学", "数理探究"), ("信息与计算科学", "数理探究"), ("物理学", "数理探究"),
                 ("化学", "数理探究"), ("生物科学", "数理探究"), ("汉语言文学（古文字学）", "阅读表达"),
                 ("历史学", "阅读表达"), ("哲学", "阅读表达")]),
    dict(name="东南大学", mode="出分前", examTime="初试6月14日左右，复试6月18日左右",
         ratio="4倍（复试资格线）", form="笔试+面试+体测",
         entry="第一类考生参加初试(笔试)，按分省各专业计划4倍划定复试资格线；第二类考生(五科奥赛全国决赛二等奖及以上)不参加初试、直接入围复试",
         entryScore="初试成绩(笔试)", note="综合成绩=高考成绩÷高考满分×850+校测成绩；校测满分150分(初试100+复试50)；复试为体测+综合面试，无笔试",
         majors=[]),
    dict(name="中国科学技术大学", mode="出分前", examTime="初试6月14日上午8:30-11:50", form="笔试+面试+体测",
         note="一类生校考满分270分(笔试200+综合面试70)；二类生面试折算270分",
         majors=[("数学类", "数学、物理"), ("物理学类", "数学、物理"), ("化学", "数学、物理"),
                 ("生物科学类", "数学、物理"), ("理论与应用力学", "数学、物理"), ("核工程类", "数学、物理"),
                 ("地球物理学", "数学、物理"), ("量子信息科学", "数学、物理"), ("能源与动力工程", "数学、物理")]),
    dict(name="浙江大学", mode="出分前", examTime="初试6月16日18:30-21:00(紫金港)，体测6月19日，面试6月20日",
         form="笔试+面试+体测", note="2026年采用晚间笔试",
         majors=[("数学与应用数学", ""), ("物理学", ""), ("工程力学", ""), ("化学", ""), ("生物工程", ""),
                 ("生物科学", ""), ("生态学", ""), ("生物育种科学", ""), ("基础医学", ""),
                 ("汉语言文学（古文字学方向）", ""), ("历史学", ""), ("哲学", "")]),
    dict(name="西安交通大学", mode="出分前", examTime="初试6月12日左右，复试6月18日左右", form="笔试+面试+体测",
         note="复试含笔试+面试，两环节各占综合成绩50%",
         majors=[("数学类", "数学、物理"), ("信息与计算科学", "数学、物理"), ("物理学", "数学、物理"),
                 ("生物技术", "数学、物理"), ("核工程与核技术", "数学、物理"), ("工程力学", "数学、物理"),
                 ("材料科学与工程", "数学、物理"), ("能源与动力工程", "数学、物理"),
                 ("储能科学与工程", "数学、物理"), ("哲学", "语文、历史")]),
    dict(name="同济大学", mode="出分前", examTime="初试6月13日14:00-16:30", form="笔试+面试+体测",
         note="学校考核满分150分：一类考生初试笔试50分+复试面试100分；初试为机考",
         majors=[("数学与应用数学", "数理综合"), ("应用物理学", "数理综合"), ("工程力学", "数理综合"),
                 ("海洋科学与技术", "数理综合"), ("应用化学", "化学"), ("生物技术", "化学")]),
    dict(name="厦门大学", mode="出分前", examTime="初试6月12日，复试6月17-18日", form="笔试+面试+体测",
         note="笔试100分、面试150分；2026年复试取消笔试(仅面试+体测)",
         majors=[("数学类", "数理综合"), ("物理学", "数理综合"), ("化学类", "数理化综合"),
                 ("生物科学类", "数理化综合"), ("海洋科学", "数理化综合"), ("药学", "数理化综合"),
                 ("历史学", "文史哲综合"), ("哲学", "文史哲综合")]),
    dict(name="北京航空航天大学", mode="出分前", examTime="初试6月12日，复试6月17-18日左右", form="笔试+面试+体测",
         note="笔试100分=数学及航空航天知识基础60分(数学基础50+航空航天10)+拔高科目40分；面试100分",
         majors=[("数学与应用数学", "数学拔高"), ("化学", "化学拔高"), ("信息与计算科学", "物理拔高"),
                 ("应用物理学", "物理拔高"), ("工程力学", "物理拔高"), ("测控技术与仪器（量子信息）", "物理拔高"),
                 ("材料科学与工程", "物理拔高"), ("航空航天类", "物理拔高")]),
    dict(name="中国人民大学", mode="出分前", examTime="初试6月13日左右，复试6月21日左右", form="笔试+面试+体测",
         note="一类考生初试60%+复试面试40%；A组考数理科技相关，B组考文史哲相关",
         majors=[("数据计算及应用", "数理科技相关"), ("汉语言文学（古文字学方向）", "文史哲相关"),
                 ("历史学类", "文史哲相关"), ("哲学", "文史哲相关")]),
    # ---------- 出分后校考 28 所 ----------
    dict(name="清华大学", mode="出分后", examTime="6月28日-7月3日综合考核", ratio="6倍",
         entry="高考成绩入围(6倍)；竞赛破格：五大学科奥赛全国决赛二等奖及以上",
         entryScore="高考成绩(不含政策加分)", form="笔试+面试+体测",
         signup="4月10日-4月30日(破格申请4月10-23日)",
         note="综合成绩满分100=高考折算85+笔试10+面试5；笔试为全国机考；分专业参考分按理科试验班/文科试验班标注",
         majors=[("数学与应用数学", "数学、物理、化学"), ("物理学", "数学、物理、化学"), ("化学", "数学、物理、化学"),
                 ("生物科学", "数学、物理、化学"), ("信息与计算科学", "数学、物理、化学"),
                 ("数理基础科学", "数学、物理、化学"), ("化学生物学", "数学、物理、化学"),
                 ("理论与应用力学", "数学、物理、化学"),
                 ("中国语言文学类（古文字学方向）", "数学、语文、历史"), ("历史学类", "数学、语文、历史"),
                 ("哲学类", "数学、语文、历史")]),
    dict(name="北京大学", mode="出分后", examTime="6月28日-7月4日考核", ratio="6倍",
         entry="高考成绩入围(6倍)；竞赛破格：五大学科奥赛全国决赛二等奖及以上",
         entryScore="高考成绩(不含政策加分)", form="笔试+面试+体测",
         signup="4月15日-4月30日(破格申请4月15-23日)",
         note="Ⅰ组/医学组笔试=数学、物理、化学；Ⅱ组笔试=语文、英语、历史",
         majors=[("数学类", "数学、物理、化学"), ("物理学类", "数学、物理、化学"), ("化学类", "数学、物理、化学"),
                 ("力学类", "数学、物理、化学"), ("生物科学类", "数学、物理、化学"),
                 ("基础医学（八年制）", "数学、物理、化学"),
                 ("历史学类", "语文、英语、历史"), ("考古学", "语文、英语、历史"),
                 ("哲学类", "语文、英语、历史"), ("中国语言文学类（古文字学方向）", "语文、英语、历史")]),
    dict(name="北京理工大学", mode="出分后", form="仅面试+体测", entry="高考成绩加权入围+单科破格",
         note="2026年取消竞赛破格；高分子材料与工程新增特种能源材料方向",
         majors=[("数学与应用数学", ""), ("应用物理学", ""), ("化学", ""), ("工程力学", ""),
                 ("智能无人系统技术", ""), ("高分子材料与工程", "")]),
    dict(name="中国农业大学", mode="出分后", form="", majors=[("生物科学", ""), ("生物育种科学", "")]),
    dict(name="北京师范大学", mode="出分后", form="", note="2026年取消竞赛破格入围通道",
         majors=[("汉语言文学（古文字学方向）", ""), ("历史学", ""), ("哲学", ""), ("数学与应用数学", ""),
                 ("物理学", ""), ("化学", ""), ("生物科学", "")]),
    dict(name="中央民族大学", mode="出分后", form="",
         majors=[("历史学", ""), ("哲学", ""), ("中国少数民族语言文学（古文字学方向）", "")]),
    dict(name="南开大学", mode="出分后", form="仅面试+体测",
         entry="高考成绩加权入围(理工类数学与物理或数学与化学1.5倍权重)+破格审核",
         note="加权示例：数学、物理按1.5倍计入入围成绩",
         majors=[("数学与应用数学", ""), ("信息与计算科学", ""), ("物理学", ""), ("化学", ""),
                 ("生物科学", ""), ("历史学", ""), ("哲学", ""), ("汉语言文学（古文字学方向）", "")]),
    dict(name="天津大学", mode="出分后", form="仅面试+体测", entry="高考成绩加权入围+单科破格",
         note="船舶与海洋工程要求高考数学≥145分且加权成绩排序6倍以内；新增船舶与海洋工程；入围需达高考满分75%",
         majors=[("数学与应用数学", ""), ("应用物理学", ""), ("应用化学", ""), ("生物科学", ""),
                 ("工程力学", ""), ("合成生物学", ""), ("能源与动力工程", ""), ("船舶与海洋工程", "")]),
    dict(name="大连理工大学", mode="出分后", form="仅面试+体测", entry="高考成绩加权入围+单科破格",
         note="2026年无竞赛破格通道",
         majors=[("数学与应用数学", ""), ("信息与计算科学", ""), ("应用物理学", ""), ("工程力学", ""),
                 ("应用化学", ""), ("生物工程", "")]),
    dict(name="东北大学", mode="出分后", form="", majors=[("自动化", "")]),
    dict(name="吉林大学", mode="出分后", examTime="2026年6月30日开始（中心校区）", ratio="6倍",
         entry="高考成绩高于特招线80分(数理化)/60分(古文字学)基础上按6倍入围；数学与应用数学高考数学≥145分可破格入围",
         entryScore="高考成绩(不含政策加分)", form="笔试+面试+体测",
         signup="4月14日-4月30日(确认校考6月12-20日)",
         note="笔试、面试满分各100分，高校考核成绩=(笔试+面试)÷2；综合成绩=高考成绩÷7.5×85%+高校考核成绩×15%；数学与应用数学含“数学与应用数学、智能科学”两套培养方案",
         majors=[("数学与应用数学", ""), ("物理学", ""), ("化学", ""), ("古文字学", "")]),
    dict(name="哈尔滨工业大学", mode="出分后", form="仅面试+体测",
         entry="高考成绩加权入围；第二类考生仅招金牌",
         note="第二类考生仅招收学科奥赛金牌；破格需审核",
         majors=[("智能装备与系统", ""), ("工程力学", ""), ("复合材料与工程（航天材料）", ""),
                 ("材料科学与工程（航天材料）", ""), ("飞行器制造工程", ""), ("储能科学与工程", ""),
                 ("核工程与核技术", ""), ("数学类", ""), ("应用物理学", "")]),
    dict(name="华东师范大学", mode="出分后", form="",
         majors=[("数学与应用数学", ""), ("物理学", ""), ("生物科学", ""), ("哲学", ""),
                 ("汉语言文学（古文字学）", "")]),
    dict(name="山东大学", mode="出分后", form="", note="2026年新增密码科学与技术",
         majors=[("数学与应用数学", ""), ("密码科学与技术", ""), ("物理学", ""), ("化学", ""),
                 ("生物科学", ""), ("生物医学科学", ""), ("汉语言文学（古文字学方向）", ""),
                 ("历史学", ""), ("哲学", "")]),
    dict(name="中国海洋大学", mode="出分后", form="仅面试+体测", entry="高考成绩加权入围",
         note="2026年无竞赛破格通道",
         majors=[("海洋科学", ""), ("海洋技术", ""), ("生物科学", "")]),
    dict(name="武汉大学", mode="出分后", form="",
         majors=[("哲学", ""), ("汉语言文学（古文字学方向）", ""), ("历史学", ""), ("数学与应用数学", ""),
                 ("物理学", ""), ("化学", ""), ("生物科学", ""), ("基础医学", ""), ("地球物理学", "")]),
    dict(name="华中科技大学", mode="出分后", form="仅面试+体测", entry="高考成绩加权入围+单科破格",
         note="2026年新增面试合格线",
         majors=[("数学与应用数学", ""), ("物理学", ""), ("化学", ""), ("生物科学", ""), ("基础医学", ""),
                 ("汉语言文学（古文字学方向）", ""), ("哲学", "")]),
    dict(name="中南大学", mode="出分后", examTime="考核7月2日前完成", ratio="5倍",
         entry="高考成绩入围(5倍，专业志愿优先)；高考数学≥145分不受名额限制、满足第一志愿直接入围；竞赛破格：五大学科奥赛全国决赛二等奖及以上",
         entryScore="高考成绩(不含政策加分)", form="仅面试+体测",
         signup="4月10日-4月30日(确认考试6月12-20日)",
         note="面试满分100分、合格线60分；综合成绩=高考85%+面试15%；体育测试不合格不予录取",
         majors=[("数学与应用数学", ""), ("应用物理学", ""), ("应用化学", ""), ("生物科学", ""),
                 ("材料科学与工程", ""), ("信息与计算科学", "")]),
    dict(name="中山大学", mode="出分后", ratio="5倍", entry="高考成绩入围(5倍)+单科破格",
         note="6个专业可凭单科成绩破格：数学≥140(数学与应用数学/物理学/生态学/理论与应用力学)、物理≥100(物理学/理论与应用力学)、化学≥100(化学/药学（生物医药）)；2026年无笔试",
         form="仅面试+体测",
         majors=[("汉语言文学（古文字学方向）", ""), ("历史学", ""), ("哲学", ""), ("数学与应用数学", ""),
                 ("物理学", ""), ("化学", ""), ("生物科学", ""), ("生态学", ""), ("基础医学", ""),
                 ("理论与应用力学", ""), ("药学（生物医药）", "")]),
    dict(name="华南理工大学", mode="出分后", form="仅面试+体测", entry="高考成绩加权入围+单科破格",
         note="2026年取消竞赛破格；数学类入围成绩=高考成绩+数学×0.4、化学类/生物技术=高考成绩+化学×0.6、应用物理学=高考成绩+物理×0.6；数学类数学≥145可破格；面试低于60分不予录取",
         majors=[("数学类", ""), ("化学类", ""), ("生物技术", ""), ("应用物理学", "")]),
    dict(name="四川大学", mode="出分后", form="",
         majors=[("汉语言文学（古文字方向）", ""), ("历史学类", ""), ("哲学", ""), ("数学与应用数学", ""),
                 ("信息与计算科学", ""), ("物理学", ""), ("工程力学", ""), ("化学", ""),
                 ("生物科学", ""), ("基础医学", "")]),
    dict(name="重庆大学", mode="出分后", form="仅面试+体测", note="2026年无竞赛破格通道",
         majors=[("数学与应用数学", ""), ("物理学", ""), ("储能科学与工程", "")]),
    dict(name="电子科技大学", mode="出分后", form="仅面试+体测", entry="高考成绩加权入围+单科破格",
         note="2026年无竞赛破格通道",
         majors=[("信息与计算科学", ""), ("数理基础科学", ""), ("应用物理学", "")]),
    dict(name="西北工业大学", mode="出分后", form="仅面试+体测", entry="高考成绩加权入围+单科破格",
         majors=[("航空航天类", ""), ("船舶与海洋工程", ""), ("数学类", ""), ("应用物理学", ""), ("化学类", "")]),
    dict(name="西北农林科技大学", mode="出分后", form="仅面试+体测", entry="高考成绩加权入围+单科破格",
         note="2026年无竞赛破格通道",
         majors=[("生物育种科学", "")]),
    dict(name="兰州大学", mode="出分后", form="仅面试+体测", entry="高考成绩加权入围+单科破格",
         note="2026年无竞赛破格通道；新增核化工与核燃料工程",
         majors=[("数学与应用数学", ""), ("物理学", ""), ("生物科学", ""), ("化学", ""),
                 ("草业科学（草类植物生物育种）", ""), ("生态学", ""), ("核化工与核燃料工程", ""),
                 ("历史学", ""), ("汉语言文学（古文字学方向）", "")]),
    dict(name="国防科技大学", mode="出分后", form="",
         majors=[("数学与应用数学", ""), ("物理学", ""), ("飞行器动力工程", "")]),
    dict(name="湖南大学", mode="出分后", form="仅面试+体测", note="2026年无竞赛破格通道",
         majors=[("化学", ""), ("应用化学", ""), ("化学生物学", "")]),
]

# ============================================================
# 组装行
# ============================================================
rows = []
for s in SCHOOLS:
    no_exam = "仅面试" in (s.get("form") or "")
    if not s["majors"]:
        rows.append(dict(school=s["name"], cat="", inc="", incRk=[], subj="无笔试" if no_exam else "",
                         score=None, rank=None, raw=""))
        continue
    for cat, subj in s["majors"]:
        inc_list, raw_hint = derive_included(cat)
        if s["name"] == "清华大学":
            sc, rk = tsinghua_ref(cat)
        else:
            sc, rk = match_major(s["name"], cat)
        rows.append(dict(
            school=s["name"], cat=cat,
            inc="、".join(inc_list), incRk=[dict(n=m, **rank_info(s["name"], m)) for m in inc_list],
            subj=("无笔试" if no_exam else subj),
            score=sc, rank=rk, raw=raw_hint,
        ))

# ============================================================
# Excel
# ============================================================
wb = Workbook()
ws1 = wb.active
ws1.title = "院校信息"
h1 = ["序号", "院校名称", "校考模式", "校考时间", "入围比例", "入围方式", "入围成绩计算",
      "校考形式", "竞赛破格政策", "报名时间", "备注"]
ws1.append(h1)
for i, s in enumerate(SCHOOLS, 1):
    ws1.append([i, s["name"], s.get("mode", ""), s.get("examTime", ""), s.get("ratio", ""),
                s.get("entry", ""), s.get("entryScore", ""), s.get("form", ""), s.get("brk", ""),
                s.get("signup", ""), s.get("note", "")])

ws2 = wb.create_sheet("专业信息")
h2 = ["序号", "院校名称", "强基专业类名称", "包含专业（顿号分隔）", "考查科目",
      "对应普通批最低分", "对应普通批最低位次", "简章原名（含方向说明）", "备注"]
ws2.append(h2)
for i, r in enumerate(rows, 1):
    ws2.append([i, r["school"], r["cat"], r["inc"], r["subj"],
                r["score"] if r["score"] else "", r["rank"] if r["rank"] else "", r["raw"], ""])

for ws, headers, widths in [
    (ws1, h1, [5, 16, 9, 34, 14, 46, 26, 15, 34, 24, 60]),
    (ws2, h2, [5, 16, 30, 34, 18, 15, 17, 30, 24]),
]:
    fill = PatternFill("solid", fgColor="1D4ED8")
    for c in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=c)
        cell.fill = fill
        cell.font = Font(color="FFFFFF", bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center")
    for c, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(c)].width = w
    ws.freeze_panes = "A2"
wb.save(OUT_SHEET)
print("已生成:", OUT_SHEET)
print("  Sheet1 院校信息:", len(SCHOOLS), "行")
print("  Sheet2 专业信息:", len(rows), "行")

# ============================================================
# data_qiangji.js
# ============================================================
out_schools = []
ri = 0
for s in SCHOOLS:
    ms = []
    for cat, subj in s["majors"]:
        r = rows[ri]; ri += 1
        ms.append({"cat": r["cat"], "inc": r["inc"], "incRk": r["incRk"], "subj": r["subj"],
                   "s": r["score"], "r": r["rank"], "raw": r["raw"]})
    if not s["majors"]:
        r = rows[ri]; ri += 1
        ms.append({"cat": "", "inc": "", "incRk": [], "subj": r["subj"], "s": None, "r": None, "raw": ""})
    out_schools.append({
        "name": s["name"], "mode": s.get("mode", ""), "examTime": s.get("examTime", ""),
        "ratio": s.get("ratio", ""), "entry": s.get("entry", ""), "entryScore": s.get("entryScore", ""),
        "form": s.get("form", ""), "brk": s.get("brk", ""), "signup": s.get("signup", ""),
        "note": s.get("note", ""), "majors": ms,
    })

with open(OUT_JS, "w", encoding="utf-8") as f:
    f.write("/* 2026 强基计划数据(公开信息预填; “待查证”字段由人工查证后合并) */\n")
    f.write("window.QJ2026=" + json.dumps({"year": 2026, "schools": out_schools}, ensure_ascii=False) + ";\n")
print("已生成:", OUT_JS)
prefilled = sum(1 for r in rows if r["inc"])
matched = sum(1 for r in rows if r["score"])
print(f"  专业行 {len(rows)}: 预填包含专业 {prefilled} 条, 分专业参考分 {matched} 条, 考查科目 "
      f"{sum(1 for r in rows if r['subj'])} 条")
print("  待查专业类(空)院校:", [s["name"] for s in SCHOOLS if not s["majors"]])
