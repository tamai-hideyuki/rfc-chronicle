import re
import time
from pathlib import Path
from typing import Optional, Any, Dict, List, Union

import requests
from requests import Response
from bs4 import BeautifulSoup
from functools import lru_cache
from tqdm.auto import tqdm

from rfc_chronicle.utils import ensure_data_dir, write_json, META_FILE

def _get_with_retry(
    url: str,
    session: requests.Session,
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    headers: Optional[dict] = None
) -> Response:
    """max_retries 回までリトライしつつ GET し、最終的に raise_for_status() する"""
    for i in range(1, max_retries + 1):
        # `timeout` を外して DummySession にも対応
        resp = session.get(url, headers=headers or {})
        if resp.status_code in (200, 304):
            return resp
        time.sleep(backoff_factor * (2 ** (i - 1)))
    resp.raise_for_status()
    return resp  # 型的に到達しない

class RFCClient:
    """
    RFC-Editor からメタデータ一覧および本文を取得し、
    ローカルにテキストを保存できるクライアント。
    """

    BASE_SEARCH_URL = "https://www.rfc-editor.org/search/rfc_search_detail.php"
    BASE_TEXT_URL = "https://www.rfc-editor.org/rfc/rfc{number}.txt"
    DEFAULT_PARAMS = {
        "pubstatus[]": "Any",
        "pub_date_type": "any",
        "page": "All",
    }
    TABLE_INDEX = 2  # メタデータ表のインデックス

    def __init__(self, session: Optional[requests.Session] = None) -> None:
        self.session = session or requests.Session()

    @staticmethod
    def _normalize_number(num_str: str) -> int:
        m = re.search(r"\d+", num_str)
        if not m:
            raise ValueError(f"Invalid RFC number: {num_str!r}")
        return int(m.group())

    @lru_cache(maxsize=1)
    def fetch_metadata(self, save: bool = False) -> List[Dict[str, Any]]:
        ensure_data_dir()
        resp = self.session.get(
            self.BASE_SEARCH_URL,
            params=self.DEFAULT_PARAMS,
            timeout=30
        )
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        tables = soup.find_all("table")
        try:
            rows = tables[self.TABLE_INDEX].find_all("tr")[1:]
        except IndexError:
            raise RuntimeError("RFC-Editor HTML structure changed")

        meta_list: List[Dict[str, Any]] = []
        for tr in tqdm(rows, desc="Parsing RFC metadata", dynamic_ncols=True):
            cols = tr.find_all("td")
            if len(cols) < 7:
                continue
            meta_list.append({
                "number": cols[0].get_text(strip=True),
                "title": cols[2].get_text(strip=True),
                "date": cols[4].get_text(strip=True),
                "status": cols[6].get_text(strip=True),
            })

        if save:
            write_json(META_FILE, meta_list)
        return meta_list

    def fetch_details(
        self,
        metadata: Dict[str, Any],
        save_dir: Path,
        use_conditional: bool = False
    ) -> Dict[str, Any]:
        """
        metadata: fetch_metadata が返す辞書 または テスト用に{'rfc_number': '0001'}の形
        save_dir: 保存先ディレクトリ (data/texts)
        use_conditional: True のとき ETag/Last-Modified で差分取得
        """
        # metadata のキーは "number" or "rfc_number" の両方をサポート
        num_str = metadata.get("number") or metadata.get("rfc_number")
        if not num_str:
            raise KeyError("metadata must contain 'number' or 'rfc_number'")
        # URL 用に整数化
        num = self._normalize_number(num_str)

        # ダウンロード先 URL を組み立て
        url = self.BASE_TEXT_URL.format(number=num)

        # 保存先ディレクトリがまだなければ作成
        save_dir.mkdir(parents=True, exist_ok=True)
        # ファイル名は元の文字列をそのまま使う
        save_path = save_dir / f"{num_str}.txt"

        # 条件付きヘッダ
        headers: Dict[str, str] = {}
        if use_conditional and save_path.exists():
            last_mod_ts = save_path.stat().st_mtime
            headers["If-Modified-Since"] = time.strftime(
                "%a, %d %b %Y %H:%M:%S GMT", time.gmtime(last_mod_ts)
            )

        # ダウンロード＆リトライ
        resp = _get_with_retry(url, self.session, headers=headers)

        # 上書き保存 or スキップ
        if resp.status_code == 200:
            save_path.write_text(resp.text, encoding="utf-8")
        # 304 の場合はファイルそのまま

        # 結果返却（本文付きのメタ情報）
        return {**metadata, "body": save_path.read_text(encoding="utf-8")}

# モジュールレベルでシングルトン
client = RFCClient()

__all__ = ["client", "RFCClient"]
