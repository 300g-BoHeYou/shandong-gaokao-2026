# -*- coding: utf-8 -*-
"""验证 /rankings/bcmr/2026/{专业代码} 页面内容是否匹配专业。"""
import re
import requests

h = {"User-Agent": "Mozilla/5.0"}
for code, expect in [("080901", "计算机科学与技术"), ("100504K", "蒙医学"), ("020101", "经济学")]:
    u = f"https://www.shanghairanking.cn/rankings/bcmr/2026/{code}"
    r = requests.get(u, headers=h, timeout=30)
    t = r.content.decode("utf-8", errors="ignore")
    title = re.search(r"<title>([^<]*)</title>", t)
    has = expect in t
    print(f"{code}: status={r.status_code} 含'{expect}'={has}  title={title.group(1)[:60] if title else '?'}")
    if not has and code == "080901":
        # 看看页面里有什么
        plain = re.sub(r"<[^>]+>", " ", t)
        plain = re.sub(r"\s+", " ", plain)
        print("  页面文本前200字:", plain[:200])
