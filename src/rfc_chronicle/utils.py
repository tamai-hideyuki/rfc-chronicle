"""
共通ユーティリティモジュール
- データディレクトリ作成
- JSON ファイル読み書き
"""
import json
from pathlib import Path

DATA_DIR = Path.home() / ".rfc_data"
META_FILE = DATA_DIR / "metadata.json"
PINS_FILE = DATA_DIR / "pins.json"


def ensure_data_dir():
    """データディレクトリが存在しなければ作成"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def read_json(file_path: Path):
    """JSON ファイルを読み込み、Python オブジェクトを返す"""
    if not file_path.exists():
        return None
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(file_path: Path, data):
    """Python オブジェクトを JSON ファイルに書き込む"""
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
