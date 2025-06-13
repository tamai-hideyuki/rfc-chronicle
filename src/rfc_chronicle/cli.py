import json
import click
from pathlib import Path
from typing import Optional, Set, List, Dict, Any

from rfc_chronicle.fetch_rfc import client as rfc_client
from rfc_chronicle.formatters import format_json, format_csv, format_md
from rfc_chronicle.utils import META_FILE

# テスト用にモック可能なピン保存先（Noneなら無効化）
PINS_FILE: Optional[Path] = None

def _load_pins() -> Set[str]:
    if not PINS_FILE or not PINS_FILE.exists():
        return set()
    return set(json.loads(PINS_FILE.read_text(encoding="utf-8")))

def _save_pins(pins: Set[str]) -> None:
    if not PINS_FILE:
        return
    PINS_FILE.write_text(json.dumps(sorted(pins), ensure_ascii=False), encoding="utf-8")

@click.group()
def cli() -> None:
    """RFC Chronicle CLI"""

@cli.command()
@click.option('-s', '--save', is_flag=True, help="ローカルにメタデータを保存")
def fetch(save: bool) -> None:
    """全 RFC のメタデータを取得"""
    try:
        meta = rfc_client.fetch_metadata(save)
        click.echo(f"Fetched {len(meta)} records.")
        if save:
            click.echo(f"Saved to {META_FILE}")
    except Exception as e:
        click.echo(f"Error fetching metadata: {e}", err=True)

@cli.command()
@click.option('--from-date', type=int, help="発行年 FROM (YYYY)")
@click.option('--to-date',   type=int, help="発行年 TO   (YYYY)")
@click.option('--keyword',   type=str, help="タイトルに含むキーワード")
def search(
    from_date: Optional[int],
    to_date:   Optional[int],
    keyword:   Optional[str],
) -> None:
    """キャッシュ済みメタデータを絞り込み検索"""
    if not META_FILE.exists():
        click.echo("No metadata cache. まずは `fetch` を実行してください。", err=True)
        return

    data: List[Dict[str, Any]] = json.loads(META_FILE.read_text(encoding="utf-8"))

    def _matches(item: Dict[str, Any]) -> bool:
        year = int(item["date"][:4])
        if from_date and year < from_date:
            return False
        if to_date   and year > to_date:
            return False
        if keyword and keyword.lower() not in item["title"].lower():
            return False
        return True

    results = [item for item in data if _matches(item)]
    click.echo(json.dumps(results, ensure_ascii=False, indent=2))

@cli.command()
@click.argument('number', type=int)
@click.option('-o', '--output', type=click.Choice(['json','csv','md']), default='md')
def show(number: int, output: str) -> None:
    """指定RFCの詳細（メタデータ＋本文）を表示"""
    try:
        details = rfc_client.fetch_details(number)
    except ValueError as e:
        click.echo(str(e), err=True)
        return

    if output == 'json':
        click.echo(format_json(details))
    elif output == 'csv':
        click.echo(format_csv(details))
    else:  # Markdown
        click.echo(f"# RFC {details['number']}: {details['title']}\n")
        click.echo(format_md([details]))

@cli.command()
@click.argument('number', type=str)
def pin(number: str) -> None:
    """RFC番号をピン（保存）"""
    pins = _load_pins()
    if number in pins:
        click.echo(f"RFC {number} is already pinned.", err=True)
        return
    pins.add(number)
    _save_pins(pins)
    click.echo(f"Pinned RFC {number}")

@cli.command()
@click.argument('number', type=str)
def unpin(number: str) -> None:
    """ピンを外す"""
    pins = _load_pins()
    if number not in pins:
        click.echo(f"RFC {number} is not pinned.", err=True)
        return
    pins.remove(number)
    _save_pins(pins)
    click.echo(f"Unpinned RFC {number}")

@cli.command('pins')
def list_pins() -> None:
    """現在ピンしているRFC一覧を表示"""
    pins = sorted(_load_pins())
    click.echo("\n".join(pins) if pins else "No pinned RFCs.")

if __name__ == "__main__":
    cli()
