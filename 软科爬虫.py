from __future__ import annotations

import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests


BASE_URL = "https://www.shanghairanking.cn"
MAJOR_API_URL = f"{BASE_URL}/api/pub/v1/bcmr/major"
RANK_API_URL = f"{BASE_URL}/api/pub/v1/bcmr/rank"
REFERER_TEMPLATE = f"{BASE_URL}/rankings/bcmr/{{year}}"
OUTPUT_DIR = Path(__file__).resolve().parent


def build_headers(year: int) -> dict[str, str]:
	return {
		"Referer": REFERER_TEMPLATE.format(year=year),
		"User-Agent": "Mozilla/5.0",
		"Accept": "application/json, text/plain, */*",
	}


def fetch_json(session: requests.Session, url: str, *, year: int, params: dict[str, object]) -> dict:
	response = session.get(url, params=params, headers=build_headers(year), timeout=20)
	response.raise_for_status()
	payload = response.json()
	if payload.get("code") != 200:
		raise RuntimeError(f"接口返回异常: {payload}")
	return payload


def fetch_json_with_requests(url: str, *, year: int, params: dict[str, object]) -> dict:
	response = requests.get(url, params=params, headers=build_headers(year), timeout=20)
	response.raise_for_status()
	payload = response.json()
	if payload.get("code") != 200:
		raise RuntimeError(f"接口返回异常: {payload}")
	return payload


def fetch_major_tree(session: requests.Session, year: int = 2026) -> list[dict]:
	"""抓取软科专业目录树。"""

	payload = fetch_json(session, MAJOR_API_URL, year=year, params={"year": year})
	return payload["data"]


def fetch_ranking_map(session: requests.Session, year: int = 2026, major_code: str = "010101") -> dict[str, int]:
	"""抓取单个专业的院校排名，返回院校名到排名的字典。"""

	payload = fetch_json(session, RANK_API_URL, year=year, params={"year": year, "majorCode": major_code})
	rankings = payload["data"]["rankings"]
	result: dict[str, int] = {}
	for item in rankings:
		ranking_text = str(item.get("ranking", "")).strip()
		if not ranking_text.isdigit():
			continue
		result["".join(str(item["univNameCn"]).split())] = int(ranking_text)
	return result


def fetch_ranking_map_fast(year: int, major_code: str) -> dict[str, int]:
	payload = fetch_json_with_requests(RANK_API_URL, year=year, params={"year": year, "majorCode": major_code})
	rankings = payload["data"]["rankings"]
	result: dict[str, int] = {}
	all_school_names: list[str] = []
	for item in rankings:
		all_school_names.append("".join(str(item["univNameCn"]).split()))
		ranking_text = str(item.get("ranking", "")).strip()
		if not ranking_text.isdigit():
			continue
		result["".join(str(item["univNameCn"]).split())] = int(ranking_text)
	if not result and all_school_names:
		return {school_name: 1 for school_name in all_school_names}
	return result


def iter_major_nodes(major_tree: list[dict]):
	for major_class in major_tree:
		for major_small_class in major_class.get("children", []) or []:
			for major in major_small_class.get("children", []) or []:
				yield major_class, major_small_class, major


def build_outputs(year: int = 2026) -> tuple[Path, Path]:
	"""生成 xlsx 和 JSON 两个输出文件。"""

	output_xlsx = OUTPUT_DIR / f"软科中国大学专业排名_{year}.xlsx"
	output_json = OUTPUT_DIR / f"软科中国大学专业排名_{year}.json"
	backup_xlsx = OUTPUT_DIR / f"软科中国大学专业排名_{year}_补1.xlsx"

	rows: list[dict[str, object]] = []
	json_tree: dict[str, dict[str, dict[str, dict[str, int]]]] = {}

	with requests.Session() as session:
		major_tree = fetch_major_tree(session, year)

	major_nodes = []
	for major_class, major_small_class, major in iter_major_nodes(major_tree):
		major_nodes.append((major_class["name"].strip(), major_small_class["name"].strip(), major["code"], major["name"].strip()))

	with ThreadPoolExecutor(max_workers=12) as executor:
		future_map = {
			executor.submit(fetch_ranking_map_fast, year, major_code): (major_class_name, major_small_class_name, major_code, major_name)
			for major_class_name, major_small_class_name, major_code, major_name in major_nodes
		}
		for future in as_completed(future_map):
			major_class_name, major_small_class_name, major_code, major_name = future_map[future]
			major_rankings = future.result()
			major_display_name = f"{major_code} {major_name}"

			json_tree.setdefault(major_class_name, {}).setdefault(major_small_class_name, {})[major_display_name] = major_rankings

			for school_name, ranking in major_rankings.items():
				rows.append(
					{
						"学校名": school_name,
						"专业名": major_display_name,
						"排名": ranking,
					}
				)

	df = pd.DataFrame(rows, columns=["学校名", "专业名", "排名"])
	try:
		df.to_excel(output_xlsx, index=False)
		xlsx_path = output_xlsx
	except PermissionError:
		df.to_excel(backup_xlsx, index=False)
		xlsx_path = backup_xlsx
	output_json.write_text(json.dumps(json_tree, ensure_ascii=False, indent=2), encoding="utf-8")
	return xlsx_path, output_json


if __name__ == "__main__":
	xlsx_path, json_path = build_outputs()
	print(f"已生成: {xlsx_path}")
	print(f"已生成: {json_path}")
