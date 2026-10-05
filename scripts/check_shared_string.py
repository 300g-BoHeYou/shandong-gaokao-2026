# -*- coding: utf-8 -*-
"""精确检查 sharedStrings 中 '45 数据计算及应用' 条目的存储内容。"""
import zipfile

with zipfile.ZipFile("2026山东高考第一批次投档.xlsx") as z:
    ss = z.read("xl/sharedStrings.xml").decode("utf-8")

# 找所有含 "45 数据计算及应用" 的位置
import re
for m in re.finditer("45 数据计算及应用", ss):
    start = m.start()
    seg = ss[start:start + 120]
    print("出现位置:", start)
    print("  原文:", repr(seg[:80]))
    print()

# 检查该条目是否完整
i = ss.find("<si><t>45 数据计算及应用")
if i >= 0:
    end = ss.find("</t></si>", i)
    print("完整条目:", repr(ss[i:end + 10]))
else:
    print("未找到 <si><t>45 数据计算及应用 开头")

# sheet xml 中该行的 t 属性(共享字符串索引)
with zipfile.ZipFile("2026山东高考第一批次投档.xlsx") as z:
    sx = z.read("xl/worksheets/sheet2.xml").decode("utf-8")
i2 = sx.find("数据计算及应用")
print("\nsheet2 中'数据计算及应用'首次出现上下文:")
print(sx[i2 - 150:i2 + 100] if i2 >= 0 else "未找到")
