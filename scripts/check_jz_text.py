# -*- coding: utf-8 -*-
"""检查已抓取简章正文质量: 去标签、关键字段命中率。"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "qj_cache"


def to_text(html):
    h = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", html, flags=re.S | re.I)
    h = re.sub(r"<br\s*/?>|</p>|</div>|</tr>|</li>|</h[1-6]>", "\n", h, flags=re.I)
    h = re.sub(r"</t[dh]>", "\t", h, flags=re.I)
    h = re.sub(r"<[^>]+>", "", h)
    h = h.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    h = re.sub(r"[ \t\u3000]+", " ", h)
    h = re.sub(r"\n\s*\n+", "\n", h)
    return h.strip()


KEY = ["入围", "破格", "笔试", "面试", "体育测试", "招生专业", "倍", "综合成绩"]


def main():
    idx = json.loads((CACHE / "jz_index.json").read_text(encoding="utf-8"))
    for name, info in idx.items():
        code = info["code"]
        best = None
        for i in range(3):
            p = CACHE / f"jz_{code}_{i}.html"
            if p.exists():
                t = to_text(p.read_text(encoding="utf-8", errors="replace"))
                if best is None or len(t) > len(best[1]):
                    best = (p.name, t)
        if not best:
            print(f"[{name}] 无缓存")
            continue
        fn, text = best
        hits = [k for k in KEY if k in text]
        wechat_block = "请在微信客户端打开" in text or "环境异常" in text or "去微信" in text
        print("=" * 78)
        print(f"[{name}] {fn} 正文 {len(text)} 字 | 命中 {len(hits)}/{len(KEY)}: {'/'.join(hits)}"
              + ("  ⚠微信占位页" if wechat_block else ""))
        print("  ", text[:260].replace("\n", " ")[:260])


if __name__ == "__main__":
    main()
