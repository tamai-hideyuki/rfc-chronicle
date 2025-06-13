import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List

from rfc_chronicle.utils import ensure_data_dir, write_json, META_FILE

BASE_SEARCH_URL = (
    "https://www.rfc-editor.org/search/rfc_search_detail.php"
    "?pubstatus%5B%5D=Any&pub_date_type=any"
)
BASE_TEXT_URL = "https://www.rfc-editor.org/rfc/rfc{number}.txt"


def fetch_metadata(save: bool = False) -> List[Dict[str, Any]]:
    """全 RFC のメタデータ一覧を取得 (番号は文字列で返す)"""
    ensure_data_dir()
    resp = requests.get(BASE_SEARCH_URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    tables = soup.find_all("table")
    if len(tables) < 3:
        raise RuntimeError("RFC‑Editor HTML 構造が変わりました")

    rows = tables[2].find_all("tr")[1:]
    meta: List[Dict[str, Any]] = []
    for tr in rows:
        cols = tr.find_all("td")
        if len(cols) < 7:
            continue
        meta.append({
            "number": cols[0].get_text(strip=True),
            "title": cols[2].get_text(strip=True),
            "date": cols[4].get_text(strip=True),
            "status": cols[6].get_text(strip=True),
        })

    if save:
        write_json(META_FILE, meta)
    return meta


def download_rfc_text(number: str) -> str:
    """指定 RFC 番号の本文を取得"""
    url = BASE_TEXT_URL.format(number=number)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def fetch_details(number: str, save_meta: bool = False) -> Dict[str, Any]:
    """指定 RFC のメタデータ + 本文を結合して返す"""
    meta_list = fetch_metadata(save=save_meta)
    try:
        meta = next(m for m in meta_list if m["number"] == number)
    except StopIteration:
        raise ValueError(f"RFC {number} が見つかりません")

    body = download_rfc_text(number)
    return {**meta, "body": body}


__all__ = ["fetch_metadata", "download_rfc_text", "fetch_details"]