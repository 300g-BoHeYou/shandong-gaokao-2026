# -*- coding: utf-8 -*-
"""补齐缺口的 5 校简章, 并组装全部 39 校语料到 qj_cache/corpus.json。"""
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "qj_cache"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36",
      "Accept-Language": "zh-CN,zh;q=0.9"}

EXTRA = {
    "华南理工大学": "https://admission.scut.edu.cn/2026/0407/c30826a622695/page.htm",
    "四川大学": "https://zs.scu.edu.cn/info/1091/3364.htm",
    "兰州大学": "https://zsb.lzu.edu.cn/zhaoshengdongtai/tongzhigonggao/2026/0409/330046.html",
    "上海交通大学": "https://admissions.sjtu.edu.cn/newDetails?contentsID=3810000004182",
}


def js_unescape(s):
    s = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)
    for a, b in [('\\"', '"'), ("\\'", "'"), ("\\/", "/"), ("\\n", "\n"), ("\\r", ""), ("\\t", " "), ("\\\\", "\\")]:
        s = s.replace(a, b)
    return s


def fetch(url, cache_name, timeout=45):
    p = CACHE / cache_name
    if p.exists() and p.stat().st_size > 800:
        return p.read_text(encoding="utf-8", errors="replace")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    enc = "utf-8"
    m = re.search(rb'charset=["\']?([\w-]+)', raw[:3000], re.I)
    if m:
        enc = m.group(1).decode("ascii", "ignore")
    try:
        text = raw.decode(enc, errors="replace")
    except LookupError:
        text = raw.decode("utf-8", errors="replace")
    p.write_text(text, encoding="utf-8")
    return text


def to_text(html):
    h = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", html, flags=re.S | re.I)
    h = re.sub(r"<br\s*/?>|</p>|</div>|</tr>|</li>|</h[1-6]>|</table>", "\n", h, flags=re.I)
    h = re.sub(r"</t[dh]>", "\t", h, flags=re.I)
    h = re.sub(r"<[^>]+>", "", h)
    h = (h.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
         .replace("&quot;", '"').replace("&#39;", "'"))
    h = re.sub(r"[ \t\u3000]+", " ", h)
    h = re.sub(r"\n\s*\n+", "\n", h)
    return h.strip()


def main():
    idx = json.loads((CACHE / "chsi_index.json").read_text(encoding="utf-8"))
    # 1) 补齐 4 校
    for name, url in EXTRA.items():
        code = idx[name]["code"]
        try:
            html = fetch(url, f"jz_{code}_x.html")
            print(f"[补齐] {name} {len(html)}B {url}")
        except Exception as e:
            print(f"[补齐失败] {name} {type(e).__name__} {e}")
        time.sleep(0.3)

    # 2) 中央民族大学附件
    mn = idx["中央民族大学"]["code"]
    chsi = (CACHE / f"chsi_{mn}.html").read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r'"(https?://[^"]+\.(?:pdf|docx?|html?))"', chsi):
        print("[民大附件候选]", m.group(1))
    for m in re.finditer(r'existFjvo:\s*(\[.*?\])', chsi, re.S):
        print("[民大 existFjvo]", m.group(1)[:400])
    for m in re.finditer(r'href=\\?"([^"\\]+)\\?"', chsi):
        u = m.group(1)
        if "chsi" not in u and u.startswith("http"):
            print("[民大外链]", u[:120])

    # 3) 组装语料
    corpus = {}
    for name, info in idx.items():
        code = info["code"]
        candidates = []
        p = CACHE / f"chsi_{code}.html"
        if p.exists():
            html = p.read_text(encoding="utf-8", errors="replace")
            m = re.search(r'content:\s*"((?:[^"\\]|\\.)*)"', html, re.S)
            if m:
                t = to_text(js_unescape(m.group(1)))
                if len(t) > 1200:
                    candidates.append(("chsi内联", t))
        for f in sorted(CACHE.glob(f"jz_{code}_*.html")):
            t = to_text(f.read_text(encoding="utf-8", errors="replace"))
            if len(t) > 1200 and "环境异常" not in t[:200]:
                candidates.append((f.name, t))
        if not candidates:
            corpus[name] = {"code": code, "signup": info.get("time", ""), "text": "", "source": ""}
            print(f"[缺失] {name}")
            continue
        src, text = max(candidates, key=lambda x: len(x[1]))
        corpus[name] = {"code": code, "signup": info.get("time", ""), "source": src, "text": text}
        print(f"[语料] {name:<10} {len(text):>6}字  来源 {src}")
    (CACHE / "corpus.json").write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")
    miss = [k for k, v in corpus.items() if not v["text"]]
    print(f"\n语料就绪 {len(corpus) - len(miss)}/{len(corpus)}; 缺失: {miss}")


if __name__ == "__main__":
    main()
