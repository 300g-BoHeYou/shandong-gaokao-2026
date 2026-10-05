# -*- coding: utf-8 -*-
"""抓取软科2026专业排名方法论页面, 提取正文与发布专业名单表格。"""
import re
import requests

url = "https://www.shanghairanking.cn/methodology/bcmr/2026"
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
print("status:", r.status_code, "len:", len(r.content))
# 页面可能 GBK 或 UTF-8
for enc in ("utf-8", "gbk"):
    try:
        t = r.content.decode(enc)
        print("decoded with", enc)
        break
    except UnicodeDecodeError:
        continue

# 找正文与表格
text = re.sub(r"<script.*?</script>", "", t, flags=re.S)
text = re.sub(r"<style.*?</style>", "", text, flags=re.S)
plain = re.sub(r"<[^>]+>", " ", text)
plain = re.sub(r"\s+", " ", plain)

# 保存正文
with open("scripts/methodology_2026.txt", "w", encoding="utf-8") as f:
    f.write(plain)
print("正文已存 scripts/methodology_2026.txt")

# 提取表格(若有专业名单)
tables = re.findall(r"<table.*?</table>", text, flags=re.S)
print("页面表格数:", len(tables))
for i, tb in enumerate(tables[:3]):
    rows = re.findall(r"<tr.*?</tr>", tb, flags=re.S)
    print(f"--- table {i}: {len(rows)} 行, 样例:", re.sub(r"<[^>]+>", "|", rows[1])[:200] if len(rows) > 1 else "")
