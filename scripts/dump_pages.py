# -*- coding: utf-8 -*-
import pdfplumber

with pdfplumber.open("本科专业目录.pdf") as pdf:
    for pi in (6, 7, 10, 11, 12, 18, 22):
        text = pdf.pages[pi].extract_text() or ""
        print(f"\n===== 第{pi+1}页 =====")
        for l in text.split("\n"):
            print(" ", repr(l))
