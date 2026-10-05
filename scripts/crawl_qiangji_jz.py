# -*- coding: utf-8 -*-
"""第二阶段: 抓取各校官方强基简章正文 (chsi 外链优先, 官方公众号兜底)。"""
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "qj_cache"

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
      "Accept-Language": "zh-CN,zh;q=0.9"}

# 官方微信公众号简章(江苏省教育考试院汇总) — 作为兜底
WECHAT = {
    "北京大学": "https://mp.weixin.qq.com/s?__biz=MzA3OTE0MjQzMw==&mid=2652034191&idx=1&sn=bb1331bbcd94c6fb515d71bf8515457e",
    "中国人民大学": "https://mp.weixin.qq.com/s?__biz=MzA3ODU4MzU3OA==&mid=2652504227&idx=1&sn=18c8b4d0139a0d6819ac09df0cab1e9a",
    "清华大学": "https://mp.weixin.qq.com/s?__biz=MzA4OTIyMzgxMw==&mid=2659401517&idx=1&sn=1a8939f9bb504acc6fe1f01e2a3079f8",
    "北京航空航天大学": "https://mp.weixin.qq.com/s?__biz=MzA3NTY1MTUzOQ==&mid=2651488755&idx=1&sn=78e3071a1058ac4f8bb53a4a307c3309",
    "北京理工大学": "https://mp.weixin.qq.com/s?__biz=MzUyMzYxNjE0Mg==&mid=2247653746&idx=1&sn=1b2c98c9a0fcdcd8ecdaea7c05639789",
    "中国农业大学": "https://mp.weixin.qq.com/s?__biz=MzA3MzM3MTUxOQ==&mid=2651285573&idx=1&sn=2e5c8920c491e9931c953eec00de74c6",
    "北京师范大学": "https://mp.weixin.qq.com/s?__biz=MjM5MTg4NjM2MQ==&mid=2658050606&idx=1&sn=95bf1324d037d15eddfcf05a359942d4",
    "中央民族大学": "https://mp.weixin.qq.com/s?__biz=MzAxNDEwNzkzMg==&mid=2651840949&idx=1&sn=86136bde471f66366ca8b07d79930ac3",
    "南开大学": "https://mp.weixin.qq.com/s?__biz=MjM5NzgwNDg0MQ==&mid=2650849867&idx=1&sn=4f30e34e45dd4b00753fb80124b7514b",
    "天津大学": "https://mp.weixin.qq.com/s?__biz=MjM5NzkwNzU0Mg==&mid=2654829695&idx=1&sn=0e93fc1c07ad21f95ae3306d0794714d",
    "大连理工大学": "https://mp.weixin.qq.com/s?__biz=MjM5MzIzODI2MA==&mid=2651909983&idx=1&sn=7200b71eb73ae90a0264ccb0b2378904",
    "东北大学": "https://mp.weixin.qq.com/s?__biz=MzA4NzIwNjIzMg==&mid=2651112701&idx=1&sn=b81ca43ffb1ff28440d95189f8627e68",
    "吉林大学": "https://mp.weixin.qq.com/s?__biz=MzUzODA1NjcyMA==&mid=2247577340&idx=1&sn=6c79ac646b148c11a0f12e7e5ef64d4f",
    "哈尔滨工业大学": "https://mp.weixin.qq.com/s?__biz=MzI3NzU5NTEwNw==&mid=2247700610&idx=1&sn=2b59d9cacfebcc9036743a817cb5a998",
    "复旦大学": "https://mp.weixin.qq.com/s?__biz=MjM5OTUwMzIwMQ==&mid=2651530990&idx=1&sn=3f3f32ee37f310c536ec9f5adfe4a272",
    "同济大学": "https://mp.weixin.qq.com/s?__biz=MzAxNzMxNzgxMQ==&mid=2656916233&idx=1&sn=b8e35f7b61328488758a36f45f810cb9",
    "上海交通大学": "https://mp.weixin.qq.com/s?__biz=MjM5MDIyMDQyMA==&mid=2650869498&idx=1&sn=3698662a6c0ed3146bfaab2994fe8d80",
    "华东师范大学": "https://mp.weixin.qq.com/s?__biz=MjM5MzY4NTMwMQ==&mid=2651604391&idx=1&sn=57159e05cb6c611183f75fb69fc9de8d",
    "南京大学": "https://mp.weixin.qq.com/s?__biz=MzAxODAzMjQ1NQ==&mid=2707754511&idx=1&sn=5ce19a08770ad4fd3da3d4400d2b0e5c",
    "东南大学": "https://mp.weixin.qq.com/s?__biz=MjM5NjQxMDE2MQ==&mid=2651046482&idx=1&sn=38a75c7039f270c856c30140ba209e2b",
    "浙江大学": "https://mp.weixin.qq.com/s?__biz=MjM5NDgxNTQwNQ==&mid=2651012201&idx=1&sn=6b3fda13c622514d801d73d475d7e9a9",
    "中国科学技术大学": "https://mp.weixin.qq.com/s?__biz=MjM5NTY5ODYyMQ==&mid=2652071906&idx=1&sn=ef3a752c953c911aac1442203ab5c726",
    "厦门大学": "https://mp.weixin.qq.com/s?__biz=MzA3OTM1MTIzNQ==&mid=2653260513&idx=1&sn=973f07612742b9bcbeebc727a775d1dc",
    "山东大学": "https://mp.weixin.qq.com/s?__biz=MzA4MTA0NTAyNw==&mid=2652300490&idx=1&sn=503462a8bc01ffa97680bf7c421f62ff",
    "中国海洋大学": "https://mp.weixin.qq.com/s?__biz=MjM5MjU2NDc0Mw==&mid=2651672109&idx=1&sn=6f96a006f49ea56db1565390c06f3b7a",
    "武汉大学": "https://mp.weixin.qq.com/s?__biz=MzA5MjM3MzUxMA==&mid=2656212784&idx=1&sn=ca2d83b88e002f39029c8d9c7bafb755",
    "华中科技大学": "https://mp.weixin.qq.com/s?__biz=MjM5MDAyMzM4MA==&mid=2650560908&idx=1&sn=2fd739c4893b4d80386bfad436425a38",
    "湖南大学": "https://mp.weixin.qq.com/s?__biz=MzA3ODQ3MjIzOA==&mid=2651823753&idx=1&sn=58545e3f871c8e38c0af60b835e1e24e",
    "中南大学": "https://mp.weixin.qq.com/s?__biz=MzA5NTI2MzExNA==&mid=2651242253&idx=1&sn=f938abb1099f1266580abe9b88140e30",
    "中山大学": "https://mp.weixin.qq.com/s?__biz=MzA3MDc5NjAyOA==&mid=2651597758&idx=1&sn=fa451b02ac3de5d82fe62ecc7d6b672d",
    "华南理工大学": "https://mp.weixin.qq.com/s?__biz=MzA5NDQ1NzE5Ng==&mid=2651568440&idx=1&sn=420a6750b04c4e41c8b5504ad542908b",
    "四川大学": "https://mp.weixin.qq.com/s?__biz=MzA5Mzc2MDYxMw==&mid=2650175673&idx=1&sn=405ab9a27b4a1833b5ac8f06f0455c57",
    "重庆大学": "https://mp.weixin.qq.com/s?__biz=MjM5MjA5MTQyMA==&mid=2651480156&idx=1&sn=02aed666cf288b4275e88c29fdcbf1d0",
    "电子科技大学": "https://mp.weixin.qq.com/s?__biz=MjM5MzM5MTMwMQ==&mid=2651769680&idx=1&sn=f672b72f879a82491df87a3fba93e305",
    "西安交通大学": "https://mp.weixin.qq.com/s?__biz=MjM5NzUxNjUyMQ==&mid=2650356875&idx=1&sn=89b41afe2cb0e47473c62c1e12689e4b",
    "西北工业大学": "https://mp.weixin.qq.com/s?__biz=MzA4NDE1MjgwNw==&mid=2649839945&idx=1&sn=49a6eee542f22e00d3d574865204139a",
    "西北农林科技大学": "https://mp.weixin.qq.com/s?__biz=MzA4MTE1MTkwNw==&mid=2651089853&idx=1&sn=7a3b96e7d715a4b5eee8c77a70213db4",
    "兰州大学": "https://mp.weixin.qq.com/s?__biz=MzA4OTQxMzUyNA==&mid=2651016404&idx=1&sn=8e7c8b262f6ff80d2869d11893e8ebc5",
    "国防科技大学": "https://mp.weixin.qq.com/s?__biz=MzAxNjYzNjkyNw==&mid=2654107743&idx=1&sn=2e8be4b6d2c80c1883bc8c12f3b07f23",
}

SKIP_HOST = ("bm.chsi.com.cn", "gaokao.chsi.com.cn", "gs.cyscc.org", "docs.qq.com", "chesicc.chsi.com.cn")


def fetch(url, cache_name, timeout=45):
    p = CACHE / cache_name
    if p.exists() and p.stat().st_size > 800:
        return p.read_text(encoding="utf-8", errors="replace"), "cache"
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
    return text, f"HTTP {len(raw)}B"


def main():
    idx = json.loads((CACHE / "chsi_index.json").read_text(encoding="utf-8"))
    report = {}
    for name, info in idx.items():
        code = info["code"]
        urls = []
        for l in info.get("links", []):
            u = l["url"]
            if u.startswith("mailto:") or any(h in u for h in SKIP_HOST):
                continue
            if u not in urls:
                urls.append(u)
        if WECHAT.get(name):
            urls.append(WECHAT[name])
        got = []
        for u in urls[:3]:
            try:
                text, note = fetch(u, f"jz_{code}_{len(got)}.html")
                got.append({"url": u, "len": len(text), "note": note})
                if len(text) > 4000:
                    break
            except urllib.error.HTTPError as e:
                got.append({"url": u, "error": f"HTTP {e.code}"})
            except Exception as e:
                got.append({"url": u, "error": f"{type(e).__name__}"})
        report[name] = {"code": code, "fetched": got}
        best = next((g for g in got if g.get("len", 0) > 4000), None)
        print(f"[{name}] " + (f"OK {best['len']}B {best['url'][:80]}" if best else
                             f"FAIL {got}"))
        time.sleep(0.3)
    (CACHE / "jz_index.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    ok = sum(1 for v in report.values() if any(g.get("len", 0) > 4000 for g in v["fetched"]))
    print(f"\n简章抓取: {ok}/{len(report)} 成功")


if __name__ == "__main__":
    main()
