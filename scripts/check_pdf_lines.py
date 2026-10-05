# -*- coding: utf-8 -*-
"""检查 PDF 中名称带前缀/换行的原始行。"""
import re
import pdfplumber

targets = ["中医儿科学", "临床药学", "信息安全", "交叉工程"]
with pdfplumber.open("本科专业目录.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text() or ""
        for raw in text.split("\n"):
            line = raw.strip()
            if any(t in line for t in targets):
                print(repr(line))
            elif re.match(r"^[A-Z]\s+\S+", line) or re.match(r"^\d{5,6}[A-Z]?$", line):
                print("  [odd]", repr(line))
