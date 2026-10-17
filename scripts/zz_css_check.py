import re
from pathlib import Path

h = Path("zongzhao.html").read_text(encoding="utf-8")
for pat in [r"header\s*\{[^}]*\}", r"header h1\s*\{[^}]*\}", r"header \.sub\s*\{[^}]*\}",
            r"\.tabbar\s*\{[^}]*\}", r"main\s*\{[^}]*\}", r"\.tab\s*\{[^}]*\}", r"footer\s*\{[^}]*\}"]:
    for m in re.finditer(pat, h):
        print(" ", m.group(0).replace("\n", " "))
print("wrap 残留:", h.count('class="wrap"'))
i = h.find("<header")
print(h[i:i + 340])
