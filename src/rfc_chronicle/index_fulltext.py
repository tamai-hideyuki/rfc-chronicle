import sqlite3
import json
import re
from pathlib import Path

# リポジトリ直下の ./data ディレクトリを基準に使用
BASE_DIR = Path.cwd() / "data"
DB_PATH = BASE_DIR / "fulltext.db"
META_PATH = BASE_DIR / "metadata.json"
TEXT_DIR = BASE_DIR / "texts"

# FTS5 テーブル名
TABLE_NAME = "rfc_text"


def _normalize_num_str(num_str: str) -> str:
    """
    メタデータの number フィールドから数字部分を抽出し、ゼロパディングなし文字列で返す
    例: "RFC 1" -> "1", "0001" -> "0001"
    """
    match = re.search(r"(\d+)", num_str)
    if not match:
        raise ValueError(f"Invalid RFC number format: {num_str}")
    return match.group(1)


def build_fulltext_db():
    """
    ./data 以下の metadata.json と texts/*.txt を読み込み、
    fulltext.db に FTS5 テーブルを作成または差分更新する。
    """
    # data ディレクトリがなければ作成
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    # データベースに接続し WAL モードに設定
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    # FTS5 用の仮想テーブルを作成（存在しない場合のみ）
    conn.execute(f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS {TABLE_NAME}
        USING fts5(
            number,      -- RFC 番号（数字文字列）
            title,       -- タイトル
            content,     -- 本文全文
            tokenize='porter'  -- Porter ステミング
        );
    """)

    # metadata.json が存在しない、または空ファイルの場合は取得・保存
    if not META_PATH.exists() or META_PATH.stat().st_size == 0:
        from rfc_chronicle.fetch_rfc import client as rfc_client
        print(f"{META_PATH} が存在しません。metadata を自動取得します...")
        meta_list = rfc_client.fetch_metadata(save=False)
        META_PATH.parent.mkdir(parents=True, exist_ok=True)
        META_PATH.write_text(json.dumps(meta_list, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"metadata saved to {META_PATH}")

    # メタデータを JSON からロード
    meta_list = json.loads(META_PATH.read_text(encoding="utf-8"))
    for entry in meta_list:
        # number キーまたは rfc_number キーをサポート
        raw_num = entry.get("number") or entry.get("rfc_number")
        # 数字部分を抽出
        num = _normalize_num_str(raw_num)
        # タイトル内のシングルクォートをエスケープ
        title = entry.get("title", "").replace("'", "''")
        # 対応するテキストファイルパス
        txt_path = TEXT_DIR / f"{num}.txt"
        if not txt_path.exists():
            # 本文が存在しない場合はスキップ
            continue
        # 本文を読み込み、シングルクォートをエスケープ
        content = txt_path.read_text(encoding="utf-8").replace("'", "''")
        # 差分更新: 既存エントリがあれば上書き
        conn.execute(f"""
            INSERT OR REPLACE INTO {TABLE_NAME}(rowid, number, title, content)
            VALUES (
                COALESCE((SELECT rowid FROM {TABLE_NAME} WHERE number = '{num}'), NULL),
                '{num}',
                '{title}',
                '{content}'
            )
        """)

    # コミットして接続を閉じる
    conn.commit()
    conn.close()


if __name__ == '__main__':
    print(f"fulltext DB を再構築中: {DB_PATH}...")
    build_fulltext_db()
    print("完了しました。")
