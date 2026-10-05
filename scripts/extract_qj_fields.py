# -*- coding: utf-8 -*-
"""从 39 校官方简章正文中抽取关键字段 -> qj_cache/extracted.json"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "qj_cache"

with open(ROOT / "scripts" / "catalog_tree.json", encoding="utf-8") as f:
    cat = json.load(f)
LEI2MAJOR, ALL_MAJOR = {}, set()
for cls in cat["tree"].values():
    for lei, majors in cls.items():
        LEI2MAJOR[lei] = [nm for _c, nm in majors]
        for _c, nm in majors:
            ALL_MAJOR.add(nm)
ALL_LEI = set(LEI2MAJOR)

CORPUS = json.loads((CACHE / "corpus.json").read_text(encoding="utf-8"))
# 补齐 4 校的额外来源
EXTRA_SRC = {
    "中央民族大学": CACHE / "fix_69437_600.html",
    "上海交通大学": CACHE / "fix_38987_52.html",
    "四川大学": CACHE / "fix_scu_jz.html",
    "兰州大学": CACHE / "lzu_jz.html",
}


def to_text(html):
    h = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", html, flags=re.S | re.I)
    h = re.sub(r"<br\s*/?>|</p>|</div>|</tr>|</li>|</h[1-6]>|</table>", "\n", h, flags=re.I)
    h = re.sub(r"</t[dh]>", "\t", h, flags=re.I)
    h = re.sub(r"<[^>]+>", "", h)
    h = (h.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
         .replace("&quot;", '"').replace("&#39;", "'"))
    h = re.sub(r"[ \t\u3000]+", " ", h)
    h = re.sub(r"\n\s*\n+", "\n", h)
    return h.strip()


def norm(s):
    """去掉简章排版中的多余空格(如 '202 6 年')"""
    return re.sub(r"\s+", "", s)


def extract(name, text):
    t = norm(text)
    out = {}
    # ---- 入围比例 ----
    m = re.search(r"按照?[^。；]{0,40}?([0-9])倍", t)
    if not m:
        m = re.search(r"([0-9])倍(?:确定|划定|以内|入围)", t)
    if not m:
        m = re.search(r"计划数的([0-9])倍", t)
    out["ratio"] = (m.group(1) + "倍") if m else ""

    # ---- 校考形式 ----
    no_exam = any(k in t for k in ["不设笔试", "无笔试", "取消笔试", "不再组织笔试", "不进行笔试", "仅面试", "只有面试"])
    has_bs = ("笔试" in t) and not no_exam
    has_ms = "面试" in t
    has_tc = ("体育测试" in t) or ("体测" in t)
    form = []
    if has_bs:
        form.append("笔试")
    if has_ms:
        form.append("面试")
    if has_tc:
        form.append("体测")
    out["form"] = ("+".join(form)) if form else ""

    # ---- 校考时间 ----
    dates = []
    for m in re.finditer(r"([0-9]{1,2})月([0-9]{1,2})日", t):
        ctx = t[max(0, m.start() - 26):m.start()]
        if any(k in ctx for k in ["考核", "测试", "初试", "复试", "笔试", "面试", "体测"]):
            d = f"{int(m.group(1))}月{int(m.group(2))}日"
            if d not in dates:
                dates.append(d)
    out["examDates"] = dates[:6]

    # ---- 笔试/考查科目 ----
    subj_names = ["数学", "物理", "化学", "生物", "语文", "历史", "哲学", "英语", "外语", "文学", "古文字"]
    exam_subj = []
    for m in re.finditer(r"笔试", t):
        seg = t[m.start():m.start() + 160]
        found = [s for s in subj_names if s in seg]
        for s in found:
            if s not in exam_subj:
                exam_subj.append(s)
    out["examSubjects"] = exam_subj[:8]

    # ---- 破格政策 ----
    brk = []
    for m in re.finditer(r"破格", t):
        seg = t[max(0, m.start() - 60):m.start() + 140]
        for k in ["取消", "不再", "二等奖", "一等奖", "金牌", "银牌", "全国决赛", "单科", "审核"]:
            if k in seg and k not in brk:
                brk.append(k)
    out["breakKeywords"] = brk

    # ---- 入围成绩计算(加权/单科) ----
    w = []
    for m in re.finditer(r"加权|单科成绩|高考成绩\+|入围成绩", t):
        seg = t[max(0, m.start() - 40):m.start() + 120]
        w.append(seg)
        if len(w) >= 2:
            break
    out["entryCalcSample"] = " | ".join(x[:110] for x in w)

    # ---- 招生专业 (目录名命中) ----
    sec = t
    m = re.search(r"招生专业(?:及|与)?(?:招生)?计划", t)
    if m:
        sec = t[m.start():m.start() + 2600]
    found_lei, found_major = [], []
    for lei in ALL_LEI:
        if lei in sec and lei not in found_lei:
            found_lei.append(lei)
    for mj in ALL_MAJOR:
        if mj in sec and mj not in found_major:
            found_major.append(mj)
    # 只保留未被更长名包含的
    def prune(names):
        names = sorted(names, key=len, reverse=True)
        keep = []
        for n in names:
            if not any(n != k and n in k for k in keep):
                keep.append(n)
        return sorted(keep)
    out["majorsInText"] = prune(found_major)
    out["leiInText"] = sorted(found_lei, key=len, reverse=True)

    # ---- 含XX、YY ----
    inc = {}
    for m in re.finditer(r"([\u4e00-\u9fa5]{2,12}类)[（(]含([^)）]{2,80})[)）]", t):
        inc[m.group(1)] = m.group(2)
    for m in re.finditer(r"([\u4e00-\u9fa5]{2,12}类)[（(]([^)）]{2,60}方向[^)）]{0,20})[)）]", t):
        inc.setdefault(m.group(1), m.group(2))
    out["includes"] = inc
    out["len"] = len(t)
    return out


def main():
    res = {}
    for name, v in CORPUS.items():
        text = v["text"]
        src = v["source"]
        extra = EXTRA_SRC.get(name)
        if (not text or len(text) < 1200) and extra and extra.exists():
            text = to_text(extra.read_text(encoding="utf-8", errors="replace"))
            src = extra.name
        if name == "兰州大学" and (not text or len(text) < 1200):
            text = to_text((CACHE / "lzu_jz.html").read_text(encoding="utf-8", errors="replace"))
            src = "lzu_jz.html"
        e = extract(name, text)
        e["source"] = src
        e["signup"] = v.get("signup", "")
        res[name] = e
    (CACHE / "extracted.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{'院校':<12}{'比例':<6}{'形式':<14}{'考核日期':<26}{'科目':<22}破格 | 来源")
    for name, e in res.items():
        print(f"{name:<12}{e['ratio']:<6}{e['form']:<14}{','.join(e['examDates'])[:24]:<26}"
              f"{'/'.join(e['examSubjects'])[:20]:<22}{'/'.join(e['breakKeywords'])[:24]} | {e['source']}")
    print("\n有招生专业命中的校数:", sum(1 for e in res.values() if e["majorsInText"]))
    print("有'含'信息的校数:", sum(1 for e in res.values() if e["includes"]))
    print("缺正文的校:", [k for k, v in res.items() if v["len"] < 800])


if __name__ == "__main__":
    main()
