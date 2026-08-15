# -*- coding: utf-8 -*-
"""诊断: 每页提取行数与未匹配行样本。"""
import re
import pdfplumber

pat_code = re.compile(r"^\d{6}[A-Z]+\s*\S")
pat_lei = re.compile(r"^\d{4}\s*\S")
pat_men = re.compile(r"^\d{2}\s*学科门类")

with pdfplumber.open("本科专业目录.pdf") as pdf:
    for pi, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        n_code = sum(1 for l in lines if pat_code.match(l))
        n_other = sum(1 for l in lines if not (pat_code.match(l) or pat_lei.match(l) or pat_men.match(l) or l.startswith(("说明", "—", "附件", "普通", "教育", "专业目录", "20", "注"))))
        print(f"p{pi+1}: lines={len(lines)} code_rows={n_code} other={n_other}")
        if n_other and pi >= 2:
            for l in lines:
                if not (pat_code.match(l) or pat_lei.match(l) or pat_men.match(l)) and not l.startswith(("—", "附件", "普通", "教育", "专业目录")):
                    print("   ", repr(l[:60]))
            print("   ---")
