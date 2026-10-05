# -*- coding: utf-8 -*-
"""查看附件接口返回内容, 并尝试更多下载路径。"""
import urllib.error
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36",
      "Referer": "https://bm.chsi.com.cn/jcxkzs/sch/10052"}


def show(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
        ctype = r.headers.get("Content-Type", "")
        disp = r.headers.get("Content-Disposition", "")
        print(f"  {r.status} {len(data):>7}B  {ctype}  {disp}  {url}")
        if "html" in ctype or data[:5] == b"<!DOC":
            body = data.decode("utf-8", "replace")
            import re
            txt = re.sub(r"<[^>]+>", " ", body)
            txt = re.sub(r"\s+", " ", txt)
            print("      正文:", txt[:200])
        else:
            print("      二进制头部:", data[:16])
        return data
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}  {url}")
    except Exception as e:
        print(f"  {type(e).__name__}  {url}")
    return None


fid = "te08hqxe21ottpyh"
for pat in [
    f"https://bm.chsi.com.cn/jcxkzs/sch/downloadFj?fileid={fid}",
    f"https://bm.chsi.com.cn/jcxkzs/sch/downfj?fileid={fid}",
    f"https://bm.chsi.com.cn/jcxkzs/sch/fjDownload?fileid={fid}",
    f"https://bm.chsi.com.cn/jcxkzs/sch/download?fileid={fid}",
    f"https://bm.chsi.com.cn/jcxkzs/sch/attachment?fileid={fid}",
    f"https://bm.chsi.com.cn/jcxkzs/sch/file?fileid={fid}",
    f"https://bm.chsi.com.cn/jcxkzs/sch/loadFj?fileid={fid}",
    f"https://bm.chsi.com.cn/jcxkzs/fj/download?fileid={fid}",
    f"https://bm.chsi.com.cn/jcxkzs/sch/viewFj?id={fid}",
]:
    show(pat)
