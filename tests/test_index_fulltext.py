import sqlite3
import json
from pathlib import Path
import shutil
import tempfile

import pytest
from rfc_chronicle.index_fulltext import build_fulltext_db, DB_PATH, TABLE_NAME

@pytest.fixture
def tmp_data_dir(monkeypatch):
    # 一時ディレクトリを data 配下としてモック
    tmp = Path(tempfile.mkdtemp())
    monkeypatch.setenv("RFC_CHRONICLE_DATA", str(tmp))
    # 必要ファイルを用意: metadata.json と texts/0001.txt
    data_dir = tmp / "data"
    meta = [{"number": "0001", "title": "TestRFC"}]
    (data_dir / "metadata.json").parent.mkdir(parents=True)
    (data_dir / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
    (data_dir / "texts").mkdir()
    (data_dir / "texts" / "0001.txt").write_text("hello world", encoding="utf-8")
    return tmp

def test_build_fulltext_db(tmp_data_dir, monkeypatch):
    # モジュールが DB_PATH を参照する場所をパッチ
    monkeypatch.setattr("rfc_chronicle.index_fulltext.DB_PATH", tmp_data_dir / "data/fulltext.db")
    from rfc_chronicle.index_fulltext import build_fulltext_db, TABLE_NAME
    # 初回
    build_fulltext_db()
    conn = sqlite3.connect(tmp_data_dir / "data/fulltext.db")
    cur = conn.execute(f"SELECT number, title, content FROM {TABLE_NAME}")
    rows = cur.fetchall()
    assert rows == [("0001", "TestRFC", "hello world")]
    conn.close()
    # 差分更新テスト: テキストを書き換えて再実行
    (tmp_data_dir / "data/texts/0001.txt").write_text("goodbye", encoding="utf-8")
    build_fulltext_db()
    conn = sqlite3.connect(tmp_data_dir / "data/fulltext.db")
    cur = conn.execute(f"SELECT content FROM {TABLE_NAME}")
    assert cur.fetchone()[0] == "goodbye"
    conn.close()
