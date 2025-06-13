"""
RFC-Editor からメタデータを取得するロジック
"""
import requests
from bs4 import BeautifulSoup
from rfc_chronicle.utils import ensure_data_dir, write_json, META_FILE

def fetch_metadata(save: bool = False) -> list[dict]:
    ensure_data_dir()
    url = (
        "https://www.rfc-editor.org/search/rfc_search_detail.php?"
        "pubstatus%5B%5D=Any&pub_date_type=any"
    )
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    tables = soup.find_all("table")
    if len(tables) < 3:
        print(f"Error: Expected at least 3 tables, found {len(tables)}.")
        return []
    target = tables[2]
    data = []
    for row in target.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) < 7:
            continue
        data.append({
            "number": cols[0].get_text(strip=True),
            "title": cols[2].get_text(strip=True),
            "date": cols[4].get_text(strip=True),
            "status": cols[6].get_text(strip=True),
        })
    if save:
        write_json(META_FILE, data)
    return data

from .fetch_rfc import fetch_metadata

__all__ = ['fetch_metadata', 'load_all_rfcs']

def load_all_rfcs():
    """
    全てのRFCメタデータを取得するラッパー関数。
    """
    return fetch_metadata()


def fetch_metadata_list(*args, **kwargs):
    """
    RFC メタデータ一覧を取得する関数。
    とりあえず空リストを返すが、後ほど実装する。
    テストではモンキーパッチされるため、このままでエラーが起きなくなる。
    """
    return []

from rfc_chronicle.fetch_rfc import fetch_metadata

def fetch_details(number: int) -> dict:
    """RFC#<number> のメタデータと本文を取得して dict で返す"""
    # メタデータ取得
    metadata = fetch_metadata(number)
    # 本文テキストをダウンロード
    body = download_rfc_text(number)
    # 結合して詳細を返す
    return {
        **metadata,
        'body': body
    }
