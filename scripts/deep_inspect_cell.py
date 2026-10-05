# -*- coding: utf-8 -*-
"""深挖齐鲁师范学院单元格: 公式? 富文本? sharedStrings 原文?"""
import openpyxl
from openpyxl.utils import get_column_letter

wb = openpyxl.load_workbook("2026山东高考第一批次投档.xlsx", data_only=False)
ws = wb["第一次投档表"]

# 找到该行
target_row = None
for row in ws.iter_rows(min_row=2):
    v = row[0].value
    if v is not None and "数据计算及应用" in str(v) and "格洛德诺" in str(v):
        target_row = row
        break

print("找到行号:", target_row[0].row)
cell = target_row[0]
print("data_only=False 值:", repr(cell.value))
print("数据类型:", cell.data_type)
print("是否公式:", isinstance(cell.value, str) and cell.value.startswith("="))
print("单元格坐标:", cell.coordinate)
# 打印整行所有单元格的原始值(非公式模式)
for c in ws[cell.row]:
    print(f"  {c.coordinate}: type={c.data_type} value={repr(c.value)}")

# 解压 xlsx 查看 sharedStrings.xml 中该条目
import zipfile, re
with zipfile.ZipFile("2026山东高考第一批次投档.xlsx") as z:
    names = z.namelist()
    print("\nzip 内文件:", names)
    if "xl/sharedStrings.xml" in names:
        ss = z.read("xl/sharedStrings.xml").decode("utf-8")
        idx = ss.find("格洛德诺")
        print("\nsharedStrings 中出现'格洛德诺'的位置:", idx)
        if idx >= 0:
            print("上下文原文:")
            print(ss[idx - 300:idx + 200])
    # 检查单元格引用: sheet xml 中该行
    sheet_xml = z.read("xl/worksheets/sheet2.xml").decode("utf-8") if "xl/worksheets/sheet2.xml" in names else None
    if sheet_xml is None:
        # 找含数据的 sheet
        for n in names:
            if n.startswith("xl/worksheets/sheet") and n.endswith(".xml"):
                sx = z.read(n).decode("utf-8")
                if "数据计算及应用" in sx:
                    print("\n所在 sheet:", n)
                    idx2 = sx.find("格洛德诺")
                    if idx2 >= 0:
                        print("sheet xml 上下文:")
                        print(sx[idx2 - 400:idx2 + 300])
                    break
