# -*- coding: utf-8 -*-
"""尝试 POST 方式下载 chsi 附件; 并直接访问民大/国防科大招生网。"""
import re
import urllib.error
import urllib.parse
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36",
      "Referer": "https://bm.chsi.com.cn/jcxkzs/sch/10052",
      "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
      "X-Requested-With": "XMLHttpRequest"}


def post(url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, headers=UA, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            d = r.read()
        print(f"  POST {r.status} {len(d):>7}B {r.headers.get('Content-Type','')} {r.headers.get('Content-Disposition','')} {url}")
        print("      ", d[:60])
        return d
    except urllib.error.HTTPError as e:
        print(f"  POST HTTP {e.code} {url}")
    except Exception as e:
        print(f"  POST {type(e).__name__} {url}")
    return None


fid = "te08hqxe21ottpyh"
for path in ["/jcxkzs/sch/downloadFj", "/jcxkzs/sch/fj", "/jcxkzs/ajaxRs", "/jcxkzs/sch/viewFj"]:
    post("https://bm.chsi.com.cn" + path, {"fileid": fid, "yxdm": "10052"})

print("\n=== 静态主机猜测 ===")
for u in [f"https://t1.chei.com.cn/bm/jcxkzs/fj/{fid}.pdf",
          f"https://t3.chei.com.cn/bm/jcxkzs/fj/{fid}.pdf",
          f"https://bm.chsi.com.cn/jcxkzs/fj/{fid}",
          f"https://bm.chsi.com.cn/jcxkzs/sch/fj/{fid}"]:
    try:
        req = urllib.request.Request(u, headers={"User-Agent": UA["User-Agent"]})
        with urllib.request.urlopen(req, timeout=25) as r:
            d = r.read()
        print(f"  {r.status} {len(d)}B {r.headers.get('Content-Type','')} {u}")
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} {u}")
    except Exception as e:
        print(f"  {type(e).__name__} {u}")

print("\n=== 民大 / 国防科大 招生网 ===")
for u in ["https://zb.muc.edu.cn/", "https://www.nudt.edu.cn/", "https://zs.nudt.edu.cn/"]:
    try:
        req = urllib.request.Request(u, headers={"User-Agent": UA["User-Agent"]})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = r.read()
        t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", d.decode("utf-8", "replace")))
        print(f"  OK {len(d)}B {u}  首段: {t[:120]}")
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} {u}")
    except Exception as e:
        print(f"  {type(e).__name__} {u}")
