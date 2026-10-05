# -*- coding: utf-8 -*-
"""补齐最后 4 校: 中央民族大学(PDF附件) / 上海交通大学(JS页) / 四川大学(412) / 兰州大学(中断)。"""
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "qj_cache"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "zh-CN,zh;q=0.9"}


def get(url, headers=None, timeout=60):
    h = dict(UA)
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


print("=== 1) 中央民族大学 PDF 附件 ===")
for cand in [
    "https://bm.chsi.com.cn/jcxkzs/sch/downloadFj?fileid=te08hqxe21ottpyh",
    "https://bm.chsi.com.cn/jcxkzs/downloadFj?fileid=te08hqxe21ottpyh",
    "https://bm.chsi.com.cn/jcxkzs/sch/fj?fileid=te08hqxe21ottpyh",
    "https://bm.chsi.com.cn/jcxkzs/sch/viewFj?fileid=te08hqxe21ottpyh",
]:
    try:
        data = get(cand, {"Referer": "https://bm.chsi.com.cn/jcxkzs/sch/10052"})
        print(f"  OK {len(data)}B  {cand}  head={data[:8]!r}")
        if len(data) > 10000:
            (CACHE / "muc_jz.pdf").write_bytes(data)
            print("  -> 已保存 muc_jz.pdf")
            break
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}  {cand}")
    except Exception as e:
        print(f"  {type(e).__name__}  {cand}")

print("\n=== 2) 上海交通大学 HTML 内是否有简章正文 ===")
p = CACHE / "jz_10248_x.html"
if p.exists():
    html = p.read_text(encoding="utf-8", errors="replace")
    print("  HTML 长度", len(html))
    for kw in ["入围", "破格", "招生专业", "笔试", "综合成绩"]:
        print(f"   '{kw}' 出现 {html.count(kw)} 次")
    m = re.search(r"(入围.{0,200})", html)
    if m:
        print("   片段:", m.group(1)[:200])
    for m in re.finditer(r'(?:contentsID|articleId|content)=([^&"\']+)', html):
        print("   参数:", m.group(0)[:80])
    for m in re.finditer(r'https?://[^"\']*\.(?:json|js)[^"\']*', html):
        u = m.group(0)
        if "admissions" in u or "api" in u:
            print("   资源:", u[:120])

print("\n=== 3) 四川大学 (带 Referer 重试) ===")
for url in ["https://zs.scu.edu.cn/info/1091/3364.htm", "https://zs.scu.edu.cn/"]:
    try:
        data = get(url, {"Referer": "https://bm.chsi.com.cn/jcxkzs/sch/10610"})
        print(f"  OK {len(data)}B {url}")
        (CACHE / f"scu_{abs(hash(url)) % 10000}.html").write_bytes(data)
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} {url}")
    except Exception as e:
        print(f"  {type(e).__name__} {url}")

print("\n=== 4) 兰州大学 重试 ===")
for url in ["https://zsb.lzu.edu.cn/zhaoshengdongtai/tongzhigonggao/2026/0409/330046.html"]:
    for attempt in range(3):
        try:
            data = get(url, {"Referer": "https://bm.chsi.com.cn/jcxkzs/sch/10730"})
            print(f"  OK {len(data)}B (第{attempt+1}次)")
            (CACHE / "lzu_jz.html").write_bytes(data)
            break
        except Exception as e:
            print(f"  第{attempt+1}次 {type(e).__name__} {e}")
            time.sleep(1.5)
