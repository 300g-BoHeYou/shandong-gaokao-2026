# -*- coding: utf-8 -*-
"""检查本科专业目录 PDF 版本(是否已更新为2026版)并重新解析。"""
import pdfplumber

with pdfplumber.open("本科专业目录.pdf") as pdf:
    print("页数:", len(pdf.pages))
    t1 = pdf.pages[0].extract_text() or ""
    print("=== 第1页 ===")
    for ln in t1.split("\n")[:12]:
        print(" ", ln)
    t2 = pdf.pages[1].extract_text() or ""
    print("\n=== 第2页前8行 ===")
    for ln in t2.split("\n")[:8]:
        print(" ", ln)
