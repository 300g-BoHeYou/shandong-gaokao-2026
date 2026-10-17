# -*- coding: utf-8 -*-
"""把综招页主题色从紫改为青绿(teal)，与一批次(蓝)、强基(紫)区分。"""
import re
from pathlib import Path

p = Path(__file__).resolve().parent.parent / "zongzhao.html"
s = p.read_text(encoding="utf-8")
before = s

# 变量
s = s.replace("--brand:#6d28d9;--brand2:#a78bfa;", "--brand:#0f766e;--brand2:#5eead4;")
# 页头渐变
s = s.replace("linear-gradient(135deg,#4c1d95,#7c3aed)", "linear-gradient(135deg,#0f766e,#14b8a6)")
# 主色/深色文字
for a, b in [
    ("#4c1d95", "#115e59"),
    ("#7c3aed", "#0f766e"),
    ("#5b21b6", "#0f766e"),
    ("#6d28d9", "#0f766e"),
    ("#a78bfa", "#5eead4"),
    ("#1d4ed8", "#0f766e"),
    # 浅底
    ("#faf5ff", "#f0fdfa"),
    ("#f5f3ff", "#ecfdf5"),
    ("#f3e8ff", "#ccfbf1"),
    ("#ede9fe", "#ccfbf1"),
    ("#ddd6fe", "#99f6e4"),
    ("#d8b4fe", "#5eead4"),
    ("#e9d5ff", "#ccfbf1"),
    ("#c4b5fd", "#5eead4"),
]:
    s = s.replace(a, b)

# 日期 chip: 用翠绿(与范围 chip 的青绿区分)
s = s.replace(".chip.date.on{background:#dbeafe;border-color:#93c5fd;color:#1e40af;}",
              ".chip.date.on{background:#d1fae5;border-color:#10b981;color:#065f46;}")

p.write_text(s, encoding="utf-8")

# 校验残留
leftovers = sorted(set(re.findall(r"#(?:4c1d95|7c3aed|5b21b6|6d28d9|a78bfa|faf5ff|f5f3ff|f3e8ff|ede9fe|ddd6fe|d8b4fe|e9d5ff|c4b5fd)", s)))
print("改动字节:", len(s) - len(before))
print("紫色残留:", leftovers if leftovers else "无")
print("teal 出现次数:", len(re.findall(r"#0f766e|#14b8a6|#115e59|#ccfbf1|#f0fdfa|#5eead4|#99f6e4|#ecfdf5", s)))
