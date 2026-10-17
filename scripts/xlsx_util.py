# -*- coding: utf-8 -*-
"""xlsx 读取工具: 展开合并单元格后按行返回 dict(避免合并区域非首行读到 None)。"""


def read_rows(path, sheet):
    from openpyxl import load_workbook
    wb = load_workbook(path, data_only=True)
    ws = wb[sheet]
    hdr = [c.value for c in ws[1]]
    # 合并区域: (min_row,min_col)->值
    span = {}
    for rng in ws.merged_cells.ranges:
        val = ws.cell(row=rng.min_row, column=rng.min_col).value
        for r in range(rng.min_row, rng.max_row + 1):
            for c in range(rng.min_col, rng.max_col + 1):
                span[(r, c)] = val
    rows = []
    for r in range(2, ws.max_row + 1):
        rec = {}
        empty = True
        for ci, h in enumerate(hdr, 1):
            if h is None:
                continue
            v = span.get((r, ci), ws.cell(row=r, column=ci).value)
            rec[h] = v
            if v not in (None, ""):
                empty = False
        if not empty:
            rows.append(rec)
    return rows
