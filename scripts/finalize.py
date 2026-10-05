# -*- coding: utf-8 -*-
"""收尾: 生成最终 强基查证清单.xlsx 与 data_qiangji.js, 并清理临时文件。

顺序:
  1) merge_official_into_sheet.py  -> 强基查证清单_官方核对.xlsx (临时: Sheet1 官方字段)
  2) split_majors.py               -> 强基查证清单.xlsx (最终: Sheet2 按专业拆分+校验)
  3) update_site_data.py           -> data_qiangji.js
  4) 清理: 临时 xlsx / 网页缓存 HTML / MHTML / 一次性探查脚本
环境变量 DRY=1 时只打印将删除的文件, 不实际删除。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
DRY = os.environ.get("DRY") == "1"

FINAL_XLSX = ROOT / "强基查证清单.xlsx"
MERGED = ROOT / "强基查证清单_官方核对.xlsx"
SPLIT = ROOT / "强基查证清单_split.xlsx"

# 1b) 精简来源信息: {校名: {code, signup, jzLink}} -> qj_cache/sources.json (随后可删 1MB 的 chsi_index.json)
CHSI_P = ROOT / "qj_cache" / "chsi_index.json"
JZ_P = ROOT / "qj_cache" / "jz_index.json"
if CHSI_P.exists():
    chsi = json.loads(CHSI_P.read_text(encoding="utf-8"))
    jz = json.loads(JZ_P.read_text(encoding="utf-8")) if JZ_P.exists() else {}
    src = {}
    for name, info in chsi.items():
        link = ""
        for g in (jz.get(name, {}).get("fetched", []) or []):
            u = g.get("url", "")
            if g.get("len", 0) > 4000 and not any(k in u for k in ("weixin", "chsi", "cyscc")):
                link = u
                break
        src[name] = {"code": info.get("code", ""), "signup": info.get("time", ""), "jzLink": link}
    if not DRY:
        (ROOT / "qj_cache" / "sources.json").write_text(json.dumps(src, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[sources] 精简来源 {len(src)} 校 -> qj_cache/sources.json")

# 1c) 把 4 校简章正文并入 corpus.json, 使其自包含(随后即可删除 HTML 缓存)
CORPUS_P = ROOT / "qj_cache" / "corpus.json"
ALT = {"中央民族大学": "fix_69437_600.html", "上海交通大学": "fix_38987_52.html",
       "四川大学": "fix_scu_jz.html", "兰州大学": "lzu_jz.html"}
if CORPUS_P.exists():
    import re
    C = json.loads(CORPUS_P.read_text(encoding="utf-8"))
    for name, fn in ALT.items():
        p = ROOT / "qj_cache" / fn
        if p.exists() and len(C.get(name, {}).get("text", "")) < 1200:
            txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", p.read_text(encoding="utf-8", errors="replace")))
            C.setdefault(name, {})["text"] = txt
            C[name]["source"] = fn
            print(f"[corpus] 并入 {name} 正文 {len(txt)} 字")
    if not DRY:
        CORPUS_P.write_text(json.dumps(C, ensure_ascii=False), encoding="utf-8")


def run(args, desc):
    print(f"\n=== {desc} ===")
    r = subprocess.run([PY, "-X", "utf8"] + args, cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    tail = "\n".join((r.stdout or "").strip().splitlines()[-14:])
    print(tail)
    if r.returncode != 0:
        print("STDERR:", (r.stderr or "")[-800:])
        raise SystemExit(f"步骤失败: {desc}")


run(["scripts/merge_official_into_sheet.py"], "合并官方字段 -> 官方核对.xlsx")
run(["scripts/split_majors.py", str(SPLIT), str(MERGED)], "按专业拆分+校验 -> split.xlsx")
if not DRY:
    import shutil
    shutil.copyfile(SPLIT, FINAL_XLSX)
    print(f"\n最终表已写入: {FINAL_XLSX}")
run(["scripts/update_site_data.py",
     str(ROOT / "data_qiangji_new.js" if DRY else ROOT / "data_qiangji.js"),
     str(FINAL_XLSX if not DRY else SPLIT)], "生成站点数据")

# 4) 清理
TO_DELETE = [ROOT / "2026年强基计划报考指南.mhtml", MERGED, SPLIT, ROOT / "data_qiangji_new.js"]
TO_DELETE += sorted((ROOT / "qj_cache").glob("*.html"))
TO_DELETE += [ROOT / "qj_cache" / n for n in ("extracted.json", "final_fields.json",
                                              "jz_index.json", "chsi_index.json")]
ONE_OFF = ["probe_chsi.py", "probe_chsi_api.py", "probe_chsi_inline.py", "probe_chsi_js.py",
           "probe_chsi_js2.py", "probe_chsi_list.py", "probe_chsi_zszc.py", "probe_attachments.py",
           "probe_fj_post.py", "probe_fj_url.py", "check_chsi_content.py", "check_jz_text.py",
           "check_time_text.py", "digest_jz.py", "extract_qj_fields.py", "extract_final.py",
           "build_corpus.py", "parse_guide_mhtml.py", "fix_missing_jz.py", "fix_lzu.py",
           "fix_last3.py", "fix_scu.py", "scan_examtime.js",
           "archive/diag_qj_ref.py", "archive/check_xmu_sjtu.py"]
TO_DELETE += [ROOT / "scripts" / n for n in ONE_OFF]

print("\n=== 清理 ===")
removed = 0
for p in TO_DELETE:
    if not p.exists():
        continue
    if DRY:
        print("  [DRY] 将删除", p.relative_to(ROOT))
    else:
        try:
            p.unlink()
            removed += 1
        except Exception as e:
            print("  删除失败", p.name, type(e).__name__)
print(f"{'[DRY] 计划' if DRY else '已'}删除 {removed if not DRY else len([p for p in TO_DELETE if p.exists()])} 个文件")
print("\n保留: qj_cache/corpus.json (39校简章正文, 供专业开设校验), qj_cache/sources.json (校代码/报名时间/官网简章链接)")
