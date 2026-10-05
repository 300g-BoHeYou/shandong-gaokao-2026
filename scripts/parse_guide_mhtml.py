# -*- coding: utf-8 -*-
"""解析 MHTML 存档, 提取各高校强基简章链接(含嵌套)。"""
import email
import html as html_mod
import quopri
import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "2026年强基计划报考指南.mhtml"

with open(SRC, "rb") as f:
    msg = email.message_from_binary_file(f)

print("MHTML 部件数:", len(list(msg.walk())))
html_parts = []
for part in msg.walk():
    ctype = part.get_content_type()
    if ctype in ("text/html", "text/plain"):
        payload = part.get_payload(decode=True)
        if payload is None:
            continue
        charset = part.get_content_charset() or "utf-8"
        try:
            text = payload.decode(charset, errors="replace")
        except LookupError:
            text = payload.decode("utf-8", errors="replace")
        html_parts.append((part.get("Content-Location", ""), ctype, len(text), text))

print("文本部件:", [(c, t, n) for c, t, n, _ in html_parts])
main = max(html_parts, key=lambda x: x[2])
print("主部件:", main[0], main[1], main[2])
doc = main[3]

# 提取链接
links = []
for m in re.finditer(r'<a\b([^>]*)>(.*?)</a>', doc, re.S | re.I):
    attrs, inner = m.group(1), m.group(2)
    href = re.search(r'href\s*=\s*["\']([^"\']+)["\']', attrs, re.I)
    if not href:
        continue
    text = html_mod.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
    links.append((text, href.group(1)))

print("\n链接总数:", len(links))
seen = set()
for text, href in links:
    key = (text, href)
    if key in seen:
        continue
    seen.add(key)
    if any(k in text for k in ("大学", "学院", "简章", "查看")) or "chsi" in href or "zsb" in href or "weixin" in href:
        print(f"  [{text[:28]}] {href[:150]}")
