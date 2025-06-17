import sqlite3
import json
import re
from pathlib import Path
from typing import List, Dict, Any
from .fetch_rfc import client as rfc_client
from rfc_chronicle.fetch_rfc import client as rfc_client

# プロジェクト直下の data ディレクトリ
BASE_DIR = Path.cwd() / "data"
DB_PATH = Path.cwd() / "data" / "fulltext.db"
META_PATH = BASE_DIR / "metadata.json"
TEXT_DIR = BASE_DIR / "texts"
TABLE_NAME = "rfc_text"


def rebuild_fulltext_index():
    from .index_fulltext import build_fulltext_db
    build_fulltext_db()

def fulltext_search(query: str):
    """
    SQLite FTS5 データベースを検索し、
    (RFC番号, マッチしたテキストの一部) を返す。
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT number, snippet(rfc_text, -1, '<b>', '</b>', '...', 5) "
        "FROM rfc_text WHERE content MATCH ? LIMIT 10",
        (query,)
    )
    results = cur.fetchall()
    conn.close()
    return results

def _normalize_num_str(num_str: str) -> str:
    """
    メタデータの number フィールドから数字部分を抽出し、ゼロパディングなし文字列で返す
    例: "RFC 1" -> "1", "0001" -> "0001"
    """
    m = re.search(r"(\d+)", num_str)
    if not m:
        raise ValueError(f"Invalid RFC number format: {num_str!r}")
    return m.group(1)


def build_fulltext_db() -> None:
    """
    ./data 以下の metadata.json と texts/*.txt を読み込み、
    fulltext.db に FTS5 テーブルを作成または差分更新する。
    """
    # data ディレクトリを作成
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    # DB接続 & WALモード設定
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")

    # FTS5 仮想テーブルを作成（存在しない場合のみ）
    conn.execute(f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS {TABLE_NAME}
        USING fts5(
            number,
            title,
            content,
            tokenize='porter'
        );
    """)

    # metadata.json がなければ自動取得
    if not META_PATH.exists() or META_PATH.stat().st_size == 0:
        print(f"{META_PATH} が見つかりません。メタデータを取得します…")
        meta_list = rfc_client.fetch_metadata(save=True)
    else:
        meta_list = json.loads(META_PATH.read_text(encoding="utf-8"))

    # テキストフォルダを作成
    TEXT_DIR.mkdir(parents=True, exist_ok=True)

    # 各エントリを差分更新
    for entry in meta_list:
        raw_num = entry.get("number") or entry.get("rfc_number")
        num = _normalize_num_str(raw_num)
        title = entry.get("title", "")

        txt_path = TEXT_DIR / f"{num}.txt"
        if not txt_path.exists():
            # 本文ファイルがなければスキップ
            continue

        content = txt_path.read_text(encoding="utf-8")

        # 既存 rowid を取得（あれば上書き用）
        cur = conn.execute(
            f"SELECT rowid FROM {TABLE_NAME} WHERE number = ?",
            (num,)
        )
        row = cur.fetchone()
        rowid = row[0] if row else None

        # INSERT OR REPLACE で差分更新（パラメタライズドクエリ）
        conn.execute(
            f"INSERT OR REPLACE INTO {TABLE_NAME}(rowid, number, title, content) VALUES (?, ?, ?, ?)",
            (rowid, num, title, content)
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    print(f"Rebuilding fulltext DB at {DB_PATH} …")
    build_fulltext_db()
    print("Done.")
