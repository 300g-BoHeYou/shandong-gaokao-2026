# -*- coding: utf-8 -*-
"""生成 综招查证清单.xlsx: 直接读取 data_zongzhao.js（与网页同源，含目录解析与软科口径）。"""
import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
s = (ROOT / "data_zongzhao.js").read_text(encoding="utf-8")
data = json.JSONDecoder().raw_decode(s[s.index("{"):])[0]
schools, meta = data["schools"], data["meta"]

HDR = ["序号", "院校名称", "范围", "院校层次", "2026计划(山东)", "报名时间", "校测日期",
       "校测形式", "校测地点", "入围比例", "综合成绩折算", "高考成绩要求",
       "招生条目数", "具体专业数", "其中软科上榜", "官方简章链接", "待核实"]
HEAD = PatternFill("solid", fgColor="5B21B6")
WARN = PatternFill("solid", fgColor="FEF3C7")

wb = Workbook()
ws = wb.active
ws.title = "综招总表"
ws.append(HDR)
for c in range(1, len(HDR) + 1):
    cell = ws.cell(row=1, column=c)
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = HEAD
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

todo = []
for i, sc in enumerate(schools, 1):
    evs = "、".join(f"{e['md']}·{e['label']}" + (f"({e['slot']})" if e.get("slot") else "")
                    for e in (sc.get("events") or [])) or "待查证"
    entries = [e for g in sc.get("groups") or [] for e in g.get("entries") or []]
    subs = [x for e in entries for x in (e.get("subs") or [])]
    nsub = sum(len(e.get("subs") or []) or 1 for e in entries)
    nrank = sum(1 for x in subs if x.get("st") == "ranked")
    gaps = []
    if sc.get("plan") is None:
        gaps.append("山东计划数")
    if not (sc.get("events") or []):
        gaps.append("校测日期")
    ws.append([i, sc["name"], sc.get("area", ""), sc.get("level", ""),
               sc.get("plan") if sc.get("plan") is not None else "待查证",
               sc.get("signup", ""), evs, sc.get("examForm", ""), sc.get("examPlace", ""),
               sc.get("ratio", ""), sc.get("score", ""), sc.get("gaokao", ""),
               len(entries), nsub, nrank, sc.get("url", ""), "；".join(gaps) or ""])
    if gaps:
        todo.append((sc["name"], "；".join(gaps)))

widths = [5, 20, 7, 22, 12, 30, 30, 30, 34, 20, 26, 30, 10, 10, 12, 46, 16]
for idx, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(idx)].width = w
for r in range(2, ws.max_row + 1):
    for c in range(1, len(HDR) + 1):
        ws.cell(row=r, column=c).alignment = Alignment(vertical="top", wrap_text=True)
    ws.row_dimensions[r].height = 44
    if ws.cell(row=r, column=len(HDR)).value:
        ws.cell(row=r, column=len(HDR)).fill = WARN
ws.freeze_panes = "C2"
ws.auto_filter.ref = f"A1:{get_column_letter(len(HDR))}{ws.max_row}"

# 第二表: 招生专业明细（含软科排名）
ws2 = wb.create_sheet("专业明细")
H2 = ["院校", "专业组", "招生专业（类）", "具体专业", "软科排名", "软科状态", "全国上榜院校数", "选考要求"]
ws2.append(H2)
for c in range(1, len(H2) + 1):
    cell = ws2.cell(row=1, column=c)
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = HEAD
STAT = {"ranked": "上榜", "unranked": "未上榜", "special": "特色专业", "notpub": "未发布",
        "nosc": "该校未收录", "nodir": "非目录专业"}
for sc in schools:
    for g in sc.get("groups") or []:
        for e in g.get("entries") or []:
            lst = e.get("subs") or []
            if not lst:
                ws2.append([sc["name"], g.get("name", ""), e["n"], e["n"], "—", "非目录/试验班", "—",
                            e.get("req", "")])
                continue
            for x in lst:
                ws2.append([sc["name"], g.get("name", ""), e["n"], x["n"],
                            x.get("rk") if x.get("st") == "ranked" else "—",
                            STAT.get(x.get("st"), ""), x.get("cnt") or "—", e.get("req", "")])
for col, w in zip("ABCDEFGH", (20, 16, 34, 30, 10, 14, 14, 20)):
    ws2.column_dimensions[col].width = w
ws2.freeze_panes = "A2"
ws2.auto_filter.ref = f"A1:H{ws2.max_row}"

ws3 = wb.create_sheet("待核实事项")
ws3.append(["序号", "院校", "待补内容", "建议来源"])
for c in range(1, 5):
    cell = ws3.cell(row=1, column=c)
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = HEAD
if todo:
    for i, (name, g) in enumerate(todo, 1):
        ws3.append([i, name, g, "学校本科招生网 / 山东省教育招生考试院《填报志愿指南》"])
else:
    ws3.append(["—", "—", "无", "—"])
for col, w in zip("ABCD", (5, 22, 26, 48)):
    ws3.column_dimensions[col].width = w

out = ROOT / "综招查证清单.xlsx"
wb.save(out)
print(f"已生成 {out.name}: {len(schools)} 所；专业明细 {ws2.max_row-1} 行；待核实 {len(todo)} 条")
for n, g in todo:
    print(f"  {n}: {g}")
