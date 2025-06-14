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

import re

def clean_rfc_text(raw: str) -> str:
    """
    フォームフィード／フッターを除去し、
    空行連続は 1 行にまとめる
    """
    lines = []
    for line in raw.splitlines():
        if line == "\f":
            continue
        if re.match(r'^[A-Za-z].+\[Page \d+\]$', line):
            continue
        if re.match(r'^RFC\s+\d+', line):
            continue
        lines.append(line.rstrip())
    cleaned = []
    prev_blank = False
    for l in lines:
        if not l.strip():
            if not prev_blank:
                cleaned.append("")
            prev_blank = True
        else:
            cleaned.append(l)
            prev_blank = False
    return "\n".join(cleaned)

def parse_rfc_header(cleaned: str) -> tuple[dict, str]:
    """
    ヘッダ部（Key: Value の行が続く部分）を
    dict として取り出し、残りを本文(body)文字列で返す
    """
    header = {}
    body_lines = []
    in_header = True
    for line in cleaned.splitlines():
        if in_header:
            if not line.strip():
                in_header = False
                continue
            m = re.match(r'^([^:]+):\s*(.+)$', line)
            if m:
                key = m.group(1).lower()
                val = m.group(2).strip()
                header[key] = header.get(key, "") + (" " + val if key in header else val)
            else:
                continue
        else:
            body_lines.append(line)
    return header, "\n".join(body_lines)