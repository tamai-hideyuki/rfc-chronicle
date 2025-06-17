from pathlib import Path
import json
from typing import List

# データ永続化ディレクトリ（プロジェクトルート/data）
DATA_DIR = Path(__file__).parent.parent / 'data'
PINS_FILE = DATA_DIR / 'pins.json'


def _load_pins() -> List[str]:
    """pins.json からピン情報を読み込む"""
    if not PINS_FILE.exists():
        return []
    try:
        return json.loads(PINS_FILE.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return []


def _save_pins(pins: List[str]) -> None:
    """pins.json にピン情報を書き込む"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PINS_FILE.write_text(
        json.dumps(pins, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )


def pin_rfc(number: str) -> None:
    """RFC番号をピンリストに追加"""
    pins = _load_pins()
    if number not in pins:
        pins.append(number)
        _save_pins(pins)


def unpin_rfc(number: str) -> None:
    """RFC番号をピンリストから削除"""
    pins = _load_pins()
    if number in pins:
        pins.remove(number)
        _save_pins(pins)


def list_pins() -> List[str]:
    """現在のピンリストを返す"""
    return _load_pins()
