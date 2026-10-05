# -*- coding: utf-8 -*-
"""最终提取: 39 校官方简章 -> qj_cache/final_fields.json (逐校关键字段+专业清单)。"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "qj_cache"

with open(ROOT / "scripts" / "catalog_tree.json", encoding="utf-8") as f:
    cat = json.load(f)
LEI2MAJOR = {}
for cls in cat["tree"].values():
    for lei, majors in cls.items():
        LEI2MAJOR[lei] = [nm for _c, nm in majors]
ALL_LEI = set(LEI2MAJOR)
ALL_MAJOR = {m for v in LEI2MAJOR.values() for m in v}

CORPUS = json.loads((CACHE / "corpus.json").read_text(encoding="utf-8"))
ALT = {
    "中央民族大学": "fix_69437_600.html",
    "上海交通大学": "fix_38987_52.html",
    "四川大学": "fix_scu_jz.html",
    "兰州大学": "lzu_jz.html",
}


def to_text(html):
    h = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", html, flags=re.S | re.I)
    h = re.sub(r"<br\s*/?>|</p>|</div>|</tr>|</li>|</h[1-6]>|</table>", "\n", h, flags=re.I)
    h = re.sub(r"</t[dh]>", "\t", h, flags=re.I)
    h = re.sub(r"<[^>]+>", "", h)
    h = (h.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
         .replace("&quot;", '"').replace("&#39;", "'"))
    h = re.sub(r"[ \t\u3000]+", " ", h)
    return re.sub(r"\n\s*\n+", "\n", h).strip()


def load_text(name):
    v = CORPUS.get(name, {})
    t = v.get("text", "")
    if len(t) < 1200 and name in ALT:
        p = CACHE / ALT[name]
        if p.exists():
            t = to_text(p.read_text(encoding="utf-8", errors="replace"))
    return re.sub(r"\s+", "", t)


def sents(t):
    return re.split(r"(?<=[。；])", t)


def find_sent(t, must, avoid=(), span=200):
    for s in sents(t):
        if all(k in s for k in must) and not any(k in s for k in avoid):
            return s[:span]
    return ""


def extract(name):
    t = load_text(name)
    o = {"len": len(t)}

    # 入围比例
    ratio, ratio_note = "", ""
    for pat, note in [(r"计划数的([0-9])倍", ""), (r"各专业组别招生计划([0-9])倍", "笔试通过比例"),
                      (r"计划([0-9])倍", ""), (r"([0-9])倍确定", ""), (r"([0-9])倍划定", "")]:
        m = re.search(pat, t)
        if m:
            ratio = m.group(1) + "倍"
            ratio_note = note
            break
    if not ratio:
        m = re.search(r"([0-9])倍", t)
        if m:
            ratio = m.group(1) + "倍"
    o["ratio"] = ratio
    o["ratioNote"] = ratio_note
    m = re.search(r"[^。；]{0,40}" + re.escape(ratio) + r"[^。；]{0,60}", t) if ratio else None
    o["ratioCtx"] = m.group(0) if m else ""

    # 校考形式
    no_exam = any(k in t for k in ["不设笔试", "无笔试", "取消笔试", "不再组织笔试", "不进行笔试", "仅有面试", "仅面试"])
    has_bs = ("笔试" in t or "初试" in t) and not no_exam
    has_ms = "面试" in t
    has_tc = ("体育测试" in t) or ("体测" in t)
    o["form"] = "+".join([x for x, c in [("笔试", has_bs), ("面试", has_ms), ("体测", has_tc)] if c])

    # 校考时间: 只取 6/7 月且上下文含考核类词
    dates, seen = [], set()
    for m in re.finditer(r"([0-9]{1,2})月([0-9]{1,2})日", t):
        mo, dd = int(m.group(1)), int(m.group(2))
        if mo not in (6, 7):
            continue
        ctx = t[max(0, m.start() - 30):m.start() + 12]
        if any(k in ctx for k in ["考核", "测试", "初试", "复试", "笔试", "面试", "入围", "公布", "打印", "确认"]):
            d = f"{mo}月{dd}日"
            if d not in seen:
                seen.add(d)
                dates.append(d)
    o["dates"] = dates[:8]
    # 关键节点句
    o["timeSents"] = [s[:150] for s in sents(t)
                      if re.search(r"[0-9]{1,2}月[0-9]{1,2}日", s) and
                      any(k in s for k in ["考核", "测试", "初试", "复试", "笔试", "面试"])][:3]

    # 笔试/考查科目
    subs = []
    for s in sents(t):
        if "笔试" in s and any(k in s for k in ["科目", "考查", "考察", "内容"]):
            for x in ["数学", "物理", "化学", "生物", "语文", "历史", "哲学", "英语", "古文字", "文学"]:
                if x in s and x not in subs:
                    subs.append(x)
    o["examSubjects"] = subs[:8]
    o["examSubjectSents"] = [s[:160] for s in sents(t)
                             if "笔试" in s and any(k in s for k in ["科目", "考查", "内容"])][:2]

    # 破格
    o["brkSents"] = [s[:170] for s in sents(t) if "破格" in s
                     and any(k in s for k in ["取消", "不再", "二等奖", "一等奖", "金牌", "银牌", "审核", "申请"])][:2]

    # 入围/成绩计算
    o["entrySents"] = [s[:170] for s in sents(t) if "入围" in s
                       and any(k in s for k in ["按照", "依据", "达到", "确定", "不低于"])][:2]
    o["calcSents"] = [s[:170] for s in sents(t) if any(k in s for k in ["加权", "单科成绩", "入围成绩=", "折算"])
                      and any(k in s for k in ["成绩", "计"])][:2]

    # 专业清单
    sec = t
    m = re.search(r"招生专业", t)
    if m:
        sec = t[m.start():m.start() + 2200]
    lei = sorted([l for l in ALL_LEI if l in sec], key=len, reverse=True)
    maj = sorted([x for x in ALL_MAJOR if x in sec], key=len, reverse=True)
    o["majorsSec"] = sec[:900]
    o["lei"] = lei[:16]
    o["majors"] = maj[:30]
    o["includes"] = {m2.group(1): m2.group(2) for m2 in
                     re.finditer(r"([\u4e00-\u9fa5]{2,12}类)[（(]含([^)）]{2,80})[)）]", t)}
    for m2 in re.finditer(r"([\u4e00-\u9fa5]{2,12}类)[（(]([^)）]{2,60}方向[^)）]{0,20})[)）]", t):
        o["includes"].setdefault(m2.group(1), m2.group(2))
    return o


res = {n: extract(n) for n in CORPUS}
(CACHE / "final_fields.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"{'院校':<11}{'比例':<5}{'形式':<12}{'考核节点(6-7月)':<30}科目")
for n, e in res.items():
    print(f"{n:<11}{e['ratio']:<5}{e['form']:<12}{','.join(e['dates'])[:28]:<30}{'/'.join(e['examSubjects'])[:24]}")
print("\n缺比例:", [n for n, e in res.items() if not e["ratio"]])
print("形式异常:", [n for n, e in res.items() if e["form"] in ("", "面试", "体测", "面试+体测")])
