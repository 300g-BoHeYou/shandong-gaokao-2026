import re
from pathlib import Path

h = Path("zongzhao.html").read_text(encoding="utf-8")
body = h[h.index("<body>"):]
body = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>|<!--[\s\S]*?-->", "", body)
opens = {}
for m in re.finditer(r"<([a-zA-Z][\w-]*)([^>]*)>", body):
    tag = m.group(1).lower()
    if m.group(2).rstrip().endswith("/") or tag in ("br", "img", "input", "meta", "link", "hr"):
        continue
    opens[tag] = opens.get(tag, 0) + 1
closes = {}
for m in re.finditer(r"</([a-zA-Z][\w-]*)>", body):
    tag = m.group(1).lower()
    closes[tag] = closes.get(tag, 0) + 1
bad = {t: (opens.get(t, 0), closes.get(t, 0)) for t in set(opens) | set(closes)
       if opens.get(t, 0) != closes.get(t, 0)}
print("不配平标签:", bad if bad else "无")
print("header 出现:", opens.get("header"), " tabbar div:", body.count('class="tabbar"'),
      " main:", opens.get("main"), closes.get("main"))
