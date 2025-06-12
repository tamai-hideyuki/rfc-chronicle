"""
RFC-Editor からメタデータを取得するロジック
"""
import requests
from bs4 import BeautifulSoup
from .utils import ensure_data_dir, write_json, META_FILE


def fetch_metadata(save: bool = False) -> list[dict]:
    """
    RFC-Editor の検索結果ページから、RFC 番号・タイトル・公開日・ステータスを抽出して返す
    - save=True の場合、.rfc_data/metadata.json にキャッシュ保存
    """
    ensure_data_dir()
    url = (
        "https://www.rfc-editor.org/search/rfc_search_detail.php?"
        "pubstatus%5B%5D=Any&pub_date_type=any"
    )
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    # 検索結果テーブルを特定（クラス名等は要確認）
    table = soup.find("table", class_="searchResults")
    data = []
    if table:
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 4:
                data.append({
                    "number": cols[0].get_text(strip=True),
                    "title": cols[1].get_text(strip=True),
                    "date": cols[2].get_text(strip=True),
                    "status": cols[3].get_text(strip=True),
                })
    # キャッシュ保存
    if save:
        write_json(META_FILE, data)
    return data
