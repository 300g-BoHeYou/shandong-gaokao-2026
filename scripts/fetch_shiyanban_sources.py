# -*- coding: utf-8 -*-
"""抓取院校官网招生专业页并 OCR 导出原始文本。

用途：为《试验班查证清单.xlsx》中的学校批量查找 2026 年本科招生专业页，
优先解析页面正文；若正文主要为图片，则下载图片并用 RapidOCR 识别。

默认先支持单校试跑，例如：
  python scripts/fetch_shiyanban_sources.py --school 上海交通大学
"""
from __future__ import annotations

import argparse
import html
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse

import requests
from openpyxl import load_workbook
from rapidocr_onnxruntime import RapidOCR


ROOT = Path(__file__).resolve().parent.parent
XLSX = ROOT / "试验班查证清单.xlsx"
OUT_DIR = ROOT / "scripts" / "shiyanban_sources"

HEADERS = {"User-Agent": "Mozilla/5.0"}
OCR = RapidOCR()


def load_school_names() -> list[str]:
    wb = load_workbook(XLSX, read_only=True)
    ws = wb.active
    names = []
    seen = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        name = str(row[2]).strip()
        if name and name not in seen:
            seen.add(name)
            names.append(name)
    return names


def search_bing(query: str) -> list[dict[str, str]]:
    url = "https://cn.bing.com/search?q=" + quote(query)
    html_text = requests.get(url, headers=HEADERS, timeout=30).text
    items: list[dict[str, str]] = []
    for m in re.finditer(r'<li class="b_algo".*?<h2[^>]*><a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html_text, re.S):
        href = html.unescape(m.group(1))
        title = re.sub(r"<.*?>", "", m.group(2))
        items.append({"title": title, "href": href})
    return items


def pick_official_result(items: list[dict[str, str]], school: str) -> dict[str, str] | None:
    keywords = ["admissions", "zsb", "zsjy", "bkzs", "bkzsw", "gk", "zhaosheng"]
    school_core = school.replace("(珠海校区)", "").replace("(威海)", "").replace("(深圳)", "")
    for item in items:
        href = item["href"]
        host = urlparse(href).netloc.lower()
        title = item["title"]
        if school_core in title or school_core in href:
            if any(k in host for k in keywords) or host.endswith(".edu.cn"):
                return item
    for item in items:
        host = urlparse(item["href"]).netloc.lower()
        if any(k in host for k in keywords):
            return item
    for item in items:
        host = urlparse(item["href"]).netloc.lower()
        if host.endswith(".edu.cn"):
            return item
    return None


def fetch_page(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    for enc in [resp.encoding, "utf-8", "gbk", "gb2312", "gb18030", resp.apparent_encoding]:
        if not enc:
            continue
        try:
            return resp.content.decode(enc)
        except Exception:
            continue
    return resp.text


def extract_image_urls(page_url: str, html_text: str) -> list[str]:
    urls: list[str] = []
    for m in re.finditer(r'<img[^>]+src="([^"]+)"', html_text, re.I):
        src = html.unescape(m.group(1))
        if src.startswith("data:"):
            continue
        abs_url = urljoin(page_url, src)
        if any(ext in abs_url.lower() for ext in (".png", ".jpg", ".jpeg", ".webp", ".gif")):
            urls.append(abs_url)
    dedup: list[str] = []
    seen = set()
    for u in urls:
        if u not in seen:
            seen.add(u)
            dedup.append(u)
    return dedup


def ocr_image(url: str) -> list[str]:
    data = requests.get(url, headers=HEADERS, timeout=60).content
    suffix = os.path.splitext(urlparse(url).path)[1] or ".png"
    path = Path(tempfile.gettempdir()) / f"shiyanban_{abs(hash(url))}{suffix}"
    path.write_bytes(data)
    result, _ = OCR(str(path))
    return [row[1].strip() for row in result or [] if str(row[1]).strip()]


def extract_text(page_url: str) -> tuple[str, list[str]]:
    html_text = fetch_page(page_url)
    # 很多招生站首页/栏目页会挂出“招生专业 / 专业一览表”等正文链接，先顺着跳到最终页面。
    target = find_target_link(page_url, html_text)
    if target and target != page_url:
        page_url = target
        html_text = fetch_page(page_url)
    images = extract_image_urls(page_url, html_text)
    if not images:
        text = re.sub(r"<script.*?</script>|<style.*?</style>", "", html_text, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text, []

    lines: list[str] = []
    for img in images:
        try:
            lines.extend(ocr_image(img))
        except Exception as exc:  # pragma: no cover - OCR is best-effort
            lines.append(f"[OCR失败] {img} :: {exc}")
    return "\n".join(lines), images


def find_target_link(page_url: str, html_text: str) -> str | None:
    """在栏目页中寻找招生专业正文链接。"""
    candidates: list[str] = []
    for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html_text, re.S | re.I):
        href = html.unescape(m.group(1))
        text = re.sub(r"<.*?>", "", m.group(2))
        if not href or href.startswith("javascript:"):
            continue
        if any(k in href or k in text for k in ["招生专业", "专业一览表", "招生计划", "招生专业类", "本科招生专业"]):
            candidates.append(urljoin(page_url, href))
    return candidates[0] if candidates else None


def score_result(item: dict[str, str], school: str) -> tuple[int, str]:
    href = item["href"]
    title = item["title"]
    score = 0
    if school in title:
        score += 20
    if "2026" in title or "2026" in href:
        score += 10
    if any(k in href.lower() for k in ["admissions", "zsb", "bkzs", "zsjy", "gk"]):
        score += 20
    if any(k in title for k in ["招生专业", "专业一览表", "招生计划"]):
        score += 15
    if any(k in href for k in ["newDetails", "detail", "article"]):
        score += 5
    return score, href


def find_source(school: str) -> dict[str, str] | None:
    queries = [
        f"{school} 2026 本科招生专业 一览表",
        f"{school} 招生专业 2026",
        f"{school} 2026 招生专业",
    ]
    candidates: list[dict[str, str]] = []
    for q in queries:
        try:
            items = search_bing(q)
        except Exception:
            continue
        if items:
            candidates.extend(items)
    if not candidates:
        return None
    official = pick_official_result(candidates, school)
    if official:
        return official
    candidates.sort(key=lambda item: score_result(item, school), reverse=True)
    return candidates[0]


def process_school(school: str) -> dict[str, object]:
    source = find_source(school)
    if not source:
        return {"school": school, "ok": False, "reason": "未找到搜索结果"}

    page_url = source["href"]
    text, images = extract_text(page_url)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[\\/:*?\"<>| ]+", "_", school)
    txt_path = OUT_DIR / f"{safe_name}.txt"
    txt_path.write_text(text, encoding="utf-8")
    return {
        "school": school,
        "ok": True,
        "source": source,
        "images": images,
        "text_path": str(txt_path),
        "text_preview": text[:1000],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--school", help="只处理单个学校")
    parser.add_argument("--url", help="直接处理指定官网/栏目页 URL")
    args = parser.parse_args()

    if args.url:
        text, images = extract_text(args.url)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[\\/:*?\"<>| ]+", "_", urlparse(args.url).netloc or "source")
        txt_path = OUT_DIR / f"{safe_name}.txt"
        txt_path.write_text(text, encoding="utf-8")
        print("url:", args.url)
        print("images:", len(images))
        print("text:", txt_path)
        print("preview:", text[:300].replace("\n", " "))
        return

    schools = [args.school] if args.school else load_school_names()
    for school in schools:
        print("==", school)
        result = process_school(school)
        if not result.get("ok"):
            print("FAIL:", result.get("reason"))
            continue
        print("source:", result["source"]["title"])
        print("url:", result["source"]["href"])
        print("images:", len(result["images"]))
        print("text:", result["text_path"])
        preview = str(result["text_preview"]).replace("\n", " ")
        print("preview:", preview[:300])


if __name__ == "__main__":
    main()