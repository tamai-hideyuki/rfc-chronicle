# src/rfc_chronicle/fetch_rfc.py

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any

from rfc_chronicle.utils import ensure_data_dir, write_json, META_FILE

BASE_SEARCH_URL = (
    "https://www.rfc-editor.org/search/rfc_search_detail.php"
    "?pubstatus%5B%5D=Any&pub_date_type=any"
)
BASE_TEXT_URL = "https://www.rfc-editor.org/rfc/rfc{number}.txt"


def fetch_metadata(save: bool = False) -> list[Dict[str, Any]]:
    """全RFCのメタデータ一覧を取得"""
    ensure_data_dir()
    resp = requests.get(BASE_SEARCH_URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    tables = soup.find_all("table")

    # 実際のデータは3番目のテーブルに格納されている想定
    if len(tables) < 3:
        raise RuntimeError(f"Expected ≥3 tables, found {len(tables)}")

    rows = tables[2].find_all("tr")[1:]
    data = []
    for tr in rows:
        cols = tr.find_all("td")
        if len(cols) < 7:
            continue
        data.append({
            "number": int(cols[0].get_text(strip=True)),
            "title": cols[2].get_text(strip=True),
            "date": cols[4].get_text(strip=True),
            "status": cols[6].get_text(strip=True),
        })

    if save:
        write_json(META_FILE, data)
    return data


def download_rfc_text(number: int) -> str:
    """指定RFC番号の本文テキストを取得"""
    url = BASE_TEXT_URL.format(number=number)
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text


def fetch_details(number: int, save_meta: bool = False) -> Dict[str, Any]:
    """
    RFC#<number> のメタデータと本文を取得して dict で返す
    - number: RFC 番号
    - save_meta: メタデータ一覧をファイルに保存するかどうか
    """
    # 1) メタデータ一覧を取得（必要なら保存）
    all_meta = fetch_metadata(save=save_meta)

    # 2) 指定番号のメタデータを検索
    try:
        meta = next(item for item in all_meta if item["number"] == number)
    except StopIteration:
        raise ValueError(f"RFC {number} のメタデータが見つかりません")

    # 3) 本文テキストを取得
    body = download_rfc_text(number)

    # 4) 結合して返却
    return {
        **meta,
        "body": body
    }


__all__ = ["fetch_metadata", "download_rfc_text", "fetch_details"]
