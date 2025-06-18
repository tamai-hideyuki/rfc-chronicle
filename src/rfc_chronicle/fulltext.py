import json
import re
import sqlite3
from pathlib import Path
from typing import List, Tuple

# プロジェクト直下の data ディレクトリ
BASE_DIR = Path.cwd() / "data"
DB_PATH = BASE_DIR / "fulltext.db"
META_PATH = BASE_DIR / "metadata.json"
TEXT_DIR = BASE_DIR / "texts"
TABLE_NAME = "rfc_text"


def _normalize_num_str(num_str: str) -> str:
    """
    メタデータの number フィールドから数字部分を抽出し、
    ゼロパディングなし文字列で返す
    例: "RFC 1" -> "1", "0001" -> "0001"
    """
    m = re.search(r"(\d+)", num_str)
    if not m:
        raise ValueError(f"Invalid RFC number format: {num_str!r}")
    return m.group(1)


def rebuild_fulltext_index() -> None:
    """
    全文検索用データベースを再構築（差分更新）する。
    """
    from .index_fulltext import build_fulltext_db
    build_fulltext_db()


def search_fulltext(query: str, limit: int = 10) -> List[Tuple[str, str]]:
    """
    data/fulltext.db の FTS5 テーブルを使って全文検索を実行し、
    [(RFC番号, 検出箇所のスニペット), …] を返す。
    """
    # クエリ文字列をエスケープせずそのまま MATCH 句に渡すことで
    # SQLite FTS5 の高度な検索構文を利用可能にする
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = lambda cursor, row: (row[0], row[1])
    cur = conn.cursor()

    sql = (
        f"SELECT number, "
        f"snippet(rfc_text, -1, '…', '…', '…', 64) "
        f"FROM {TABLE_NAME} "
        f"WHERE content MATCH ? "
        f"LIMIT ?"
    )
    cur.execute(sql, (query, limit))
    results = cur.fetchall()
    conn.close()
    return results


def build_fulltext_db() -> None:
    """
    ./data 以下の metadata.json と texts/*.txt を読み込み、
    fulltext.db に FTS5 テーブルを作成または差分更新する。
    """
    # data ディレクトリを作成
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    # DB 接続 & WAL モード設定
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")

    # FTS5 仮想テーブルを作成（存在しない場合のみ）
    conn.execute(f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS {TABLE_NAME}
        USING fts5(
            number,
            title,
            content,
            tokenize = 'porter'
        );
    """)

    # metadata.json がなければ自動取得
    if not META_PATH.exists() or META_PATH.stat().st_size == 0:
        from .fetch_rfc import client as rfc_client
        meta_list = rfc_client.fetch_metadata(save=True)
    else:
        meta_list = json.loads(META_PATH.read_text(encoding="utf-8"))

    # texts ディレクトリを作成
    TEXT_DIR.mkdir(parents=True, exist_ok=True)

    # 各 RFC 本文を差分更新
    for entry in meta_list:
        raw_num = entry.get("number") or entry.get("rfc_number", "")
        try:
            num = _normalize_num_str(raw_num)
        except ValueError:
            continue  # フォーマット不整合はスキップ

        txt_path = TEXT_DIR / f"{num}.txt"
        if not txt_path.exists():
            continue  # 本文ファイルが無ければスキップ

        title = entry.get("title", "")
        content = txt_path.read_text(encoding="utf-8")

        # 既存 rowid を取得（あれば上書き）
        cur = conn.execute(
            f"SELECT rowid FROM {TABLE_NAME} WHERE number = ?",
            (num,)
        )
        row = cur.fetchone()
        rowid = row[0] if row else None

        # INSERT OR REPLACE で差分更新
        conn.execute(
            f"INSERT OR REPLACE INTO {TABLE_NAME} (rowid, number, title, content) "
            f"VALUES (?, ?, ?, ?)",
            (rowid, num, title, content)
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    print(f"Rebuilding fulltext DB at {DB_PATH} …")
    build_fulltext_db()
    print("Done.")
