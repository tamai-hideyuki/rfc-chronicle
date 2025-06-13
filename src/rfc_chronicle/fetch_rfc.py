import re
import requests
from bs4 import BeautifulSoup
from functools import lru_cache
from typing import Any, Dict, List, Union
from pathlib import Path

from rfc_chronicle.utils import ensure_data_dir, write_json, META_FILE

class RFCClient:
    """
    RFC-Editor からメタデータ一覧および本文を取得するクライアント。
    """

    BASE_SEARCH_URL = "https://www.rfc-editor.org/search/rfc_search_detail.php"
    DEFAULT_PARAMS = {
        "pubstatus[]": "Any",       # 全ステータス
        "pub_date_type": "any",     # 全期間
        "page": "All",              # 全件取得
    }
    BASE_TEXT_URL = "https://www.rfc-editor.org/rfc/rfc{number}.txt"
    TABLE_INDEX = 2  # メタデータ表があるテーブルのインデックス（0始まり）

    def __init__(self, session: requests.Session = None) -> None:
        self.session = session or requests.Session()

    @staticmethod
    def _normalize_number(num_str: str) -> int:
        """
        "RFC 1" や "1" のような表記から最初の数字部分を抽出し int 化。
        数字が見つからなければ ValueError を投げる。
        """
        match = re.search(r"\d+", num_str)
        if not match:
            raise ValueError(f"Invalid RFC number: {num_str!r}")
        return int(match.group())

    @lru_cache(maxsize=1)
    def fetch_metadata(self, save: bool = False) -> List[Dict[str, Any]]:
        """
        全 RFC のメタデータ一覧を取得し、必要ならローカル保存。
        戻り値の 'number' は文字列のまま。
        """
        ensure_data_dir()
        response = self.session.get(
            self.BASE_SEARCH_URL,
            params=self.DEFAULT_PARAMS,
            timeout=30,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        tables = soup.find_all("table")
        try:
            rows = tables[self.TABLE_INDEX].find_all("tr")[1:]
        except IndexError:
            raise RuntimeError("RFC-Editor HTML 構造が変わりました")

        meta_list: List[Dict[str, Any]] = []
        for tr in rows:
            cols = tr.find_all("td")
            if len(cols) < 7:
                continue
            meta_list.append({
                "number": cols[0].get_text(strip=True),
                "title":  cols[2].get_text(strip=True),
                "date":   cols[4].get_text(strip=True),
                "status": cols[6].get_text(strip=True),
            })

        if save:
            write_json(META_FILE, meta_list)
        return meta_list

    def download_rfc_text(self, number: Union[int, str]) -> str:
        """
        指定した RFC 番号の本文を取得。
        number は int または文字列で可。
        """
        num = int(number)
        url = self.BASE_TEXT_URL.format(number=num)
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.text

    def fetch_details(
        self,
        number: Union[int, str],
        save_meta: bool = False,
    ) -> Dict[str, Any]:
        """
        指定RFCのメタデータと本文を結合して返す。
        存在しない番号なら ValueError。
        """
        num = int(number)
        meta_list = self.fetch_metadata(save_meta)
        try:
            meta = next(
                m for m in meta_list
                if self._normalize_number(m["number"]) == num
            )
        except StopIteration:
            raise ValueError(f"RFC {num} が見つかりません")

        body = self.download_rfc_text(num)
        return {**meta, "body": body}

# モジュールレベルでシングルトン
client = RFCClient()

__all__ = ["client", "RFCClient"]
