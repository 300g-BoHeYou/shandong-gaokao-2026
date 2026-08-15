# -*- coding: utf-8 -*-
"""检查2026版目录中 交叉工程/区域国别学 等专业是否被解析遗漏。"""
import re
import pdfplumber

targets = ["交叉工程", "区域国别学", "智能医学工程", "未来机器人", "集成电路", "碳中和", "语言学", "低空技术与工程", "智慧城市"]

with pdfplumber.open("本科专业目录.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text() or ""
        for raw in text.split("\n"):
            line = raw.strip()
            if any(t in line for t in targets):
                print(repr(line))

# 顺便看 交叉学科 门类的完整段落
print("\n== 含'交叉'的行 ==")
with pdfplumber.open("本科专业目录.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text() or ""
        for raw in text.split("\n"):
            line = raw.strip()
            if "交叉" in line:
                print(repr(line))
