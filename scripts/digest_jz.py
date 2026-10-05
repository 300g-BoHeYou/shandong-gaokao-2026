# -*- coding: utf-8 -*-
"""生成每校关键句复核摘录(控制篇幅, 便于校核)。"""
import json
import re
import sys
from pathlib import Path

CACHE = Path(__file__).resolve().parent.parent / "qj_cache"
CORPUS = json.loads((CACHE / "corpus.json").read_text(encoding="utf-8"))
EX = json.loads((CACHE / "extracted.json").read_text(encoding="utf-8"))

with open(Path(__file__).resolve().parent / "catalog_tree.json", encoding="utf-8") as f:
    cat = json.load(f)
LEI = set()
for cls in cat["tree"].values():
    LEI.update(cls.keys())


def norm(s):
    return re.sub(r"\s+", "", s)


def digest(name):
    text = CORPUS.get(name, {}).get("text", "")
    if len(text) < 1200:
        p = Path(__file__).resolve().parent.parent / "qj_cache"
        for cand in ["fix_69437_600.html", "fix_38987_52.html", "fix_scu_jz.html", "lzu_jz.html"]:
            c = p / cand
            if c.exists():
                h = c.read_text(encoding="utf-8", errors="replace")
                t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h))
                if name[:4] in t[:2000]:
                    text = t
                    break
    t = norm(text)
    out = [f"【{name}】 报名 {EX[name]['signup']}  来源 {EX[name]['source']}  正文{len(t)}字"]

    # 入围比例上下文
    m = re.search(r"[^。；]{0,60}?[0-9]倍[^。；]{0,40}", t)
    out.append("  比例: " + (m.group(0) if m else "未命中"))
    # 入围成绩计算
    for m in re.finditer(r"[^。；]{0,50}(?:加权|单科成绩|入围成绩|折算)[^。；]{0,90}", t):
        seg = m.group(0)
        if any(k in seg for k in ["加权", "入围成绩", "单科"]):
            out.append("  计算: " + seg[:150])
            break
    # 校考形式/科目
    for kw in ["初试", "笔试", "考核", "面试"]:
        m = re.search(rf"[^。；]{{0,40}}{kw}[^。；]{{0,110}}", t)
        if m:
            out.append(f"  {kw}: " + m.group(0)[:150])
    # 破格
    m = re.search(r"[^。；]{0,60}破格[^。；]{0,110}", t)
    if m:
        out.append("  破格: " + m.group(0)[:160])
    # 招生专业
    sec = ""
    m = re.search(r"招生专业[^。]{0,40}", t)
    if m:
        sec = t[m.start():m.start() + 700]
    hit_lei = [l for l in sorted(LEI, key=len, reverse=True) if l in sec]
    out.append("  专业段: " + sec[:260])
    out.append("  含大类: " + "、".join(hit_lei[:14]))
    return "\n".join(out)


targets = sys.argv[1:] if len(sys.argv) > 1 else list(CORPUS.keys())
for n in targets:
    print(digest(n))
    print("-" * 100)
