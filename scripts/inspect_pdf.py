# -*- coding: utf-8 -*-
"""解析本科专业目录 PDF, 输出文本结构与基本信息。"""
import pdfplumber

path = "本科专业目录.pdf"
with pdfplumber.open(path) as pdf:
    print("页数:", len(pdf.pages))
    for pi, page in enumerate(pdf.pages[:5]):
        text = page.extract_text() or ""
        lines = text.split("\n")
        print(f"\n=== 第{pi+1}页 前20行 ===")
        for ln in lines[:20]:
            print(" ", ln)
    # 最后一页
    last = pdf.pages[-1].extract_text() or ""
    print("\n=== 最后一页 后10行 ===")
    for ln in last.split("\n")[-10:]:
        print(" ", ln)
