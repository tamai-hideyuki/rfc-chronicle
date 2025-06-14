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
from rfc_chronicle.utils import clean_rfc_text, parse_rfc_header


def _get_with_retry(
    url: str,
    session: requests.Session,
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    headers: Optional[dict] = None
) -> Response:
    """指定回数リトライしつつGETを実行、最終的に例外を投げる"""
    headers = headers or {}
    for attempt in range(1, max_retries + 1):
        resp = session.get(url, headers=headers)
        if resp.status_code in (200, 304):
            return resp
        time.sleep(backoff_factor * (2 ** (attempt - 1)))
    resp.raise_for_status()


class RFCClient:
    """
    RFC メタデータと本文を取得・ローカル保存するクライアント
    """

    BASE_SEARCH_URL = "https://www.rfc-editor.org/search/rfc_search_detail.php"
    BASE_TEXT_URL = "https://www.rfc-editor.org/rfc/rfc{number}.txt"
    DEFAULT_PARAMS = {
        "pubstatus[]": "Any",
        "pub_date_type": "any",
        "page": "All",
    }
    TABLE_INDEX = 2  # メタデータ表インデックス

    def __init__(self, session: Optional[requests.Session] = None) -> None:
        self.session = session or requests.Session()

    @staticmethod
    def _normalize_number(num_str: str) -> int:
        """RFC番号文字列から整数部を抽出"""
        match = re.search(r"(\d+)", num_str)
        if not match:
            raise ValueError(f"Invalid RFC number: {num_str!r}")
        return int(match.group(1))

    @lru_cache(maxsize=1)
    def fetch_metadata(self, save: bool = False) -> List[Dict[str, Any]]:
        """
        RFC-Editorからメタデータ一覧を取得し、必要ならローカル保存
        """
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
            # 各カラムを取得
            number = cols[0].get_text(strip=True)
            title = cols[2].get_text(strip=True)
            date = cols[4].get_text(strip=True)
            status = cols[6].get_text(strip=True)
            meta_list.append({
                "number": number,
                "title": title,
                "date": date,
                "status": status,
            })

        if save:
            write_json(META_FILE, meta_list)
        return meta_list




    def fetch_details(
            self,
            metadata: Union[int, str, Dict[str, Any]],
            save_dir: Path,
            use_conditional: bool = False
        ) -> Dict[str, Any]:
            """
            指定RFCの本文をダウンロード・保存し、
            ヘッダをパースしてmetadataにマージしたdictを返す。
            """
            # --- 1. metadata を dict に統一 ---
            if not isinstance(metadata, dict):
                metadata = {"number": str(metadata)}

            raw_num = metadata.get("number") or metadata.get("rfc_number")
            num = self._normalize_number(raw_num)
            target = save_dir / f"{num}.txt"
            save_dir.mkdir(parents=True, exist_ok=True)

            # --- 2. 条件付きダウンロードヘッダ ---
            headers: Dict[str, str] = {}
            if use_conditional and target.exists():
                ts = target.stat().st_mtime
                headers["If-Modified-Since"] = time.strftime(
                    "%a, %d %b %Y %H:%M:%S GMT",
                    time.gmtime(ts)
                )

            # --- 3. ダウンロード & ファイル保存 ---
            url = self.BASE_TEXT_URL.format(number=num)
            resp: Response = _get_with_retry(url, self.session, headers=headers)
            if resp.status_code == 200:
                target.write_text(resp.text, encoding="utf-8")

            # --- 4. テキストのクリーン & ヘッダパース ---
            raw = target.read_text(encoding="utf-8")
            cleaned = clean_rfc_text(raw)
            header_dict, body = parse_rfc_header(cleaned)

            # --- 5. metadata 更新 & 返却 ---
            metadata.update(header_dict)
            metadata["body"] = body
            return metadata


# シングルトンインスタンス
client = RFCClient()
__all__ = ["client", "RFCClient"]
