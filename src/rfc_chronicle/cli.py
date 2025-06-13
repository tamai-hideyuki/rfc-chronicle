import json
import click
from pathlib import Path

from rfc_chronicle.fetch_rfc import (
    fetch_metadata,
    fetch_details,
    fetch_metadata as load_all_rfcs,  # tests が monkeypatch する
)
from rfc_chronicle.formatters import format_json, format_csv, format_md

# ===== pins 用スタブ / 定数 =====
PINS_FILE: Path | None = None  # tests で monkeypatch される

def _load_pins() -> set[str]:
    if PINS_FILE is None or not PINS_FILE.exists():
        return set()
    return set(json.loads(PINS_FILE.read_text(encoding="utf-8")))

def _save_pins(pins: set[str]) -> None:
    if PINS_FILE is None:
        return
    PINS_FILE.write_text(json.dumps(sorted(pins)), encoding="utf-8")
# =================================

@click.group()
def cli() -> None:
    """RFC Chronicle CLI"""
    pass

# ---------- fetch コマンド ----------
@cli.command("fetch")
@click.option("-s", "--save", is_flag=True, help="メタデータを data ディレクトリへ保存")
def fetch(save: bool) -> None:  # ★ tests は cli.fetch を import する
    """全 RFC メタデータを取得し件数を出力"""
    try:
        meta = fetch_metadata(save=save)
        click.echo(f"Fetched {len(meta)} records.")
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)

# ---------- search コマンド ----------
@cli.command("search")
@click.option("--from-date")
@click.option("--to-date")
@click.option("--keyword")
def search(from_date: str | None, to_date: str | None, keyword: str | None) -> None:
    from rfc_chronicle.utils import META_FILE

    if not META_FILE.exists():
        click.echo("No metadata cache.", err=True)
        return

    data = json.loads(META_FILE.read_text(encoding="utf-8"))
    results = []
    for item in data:
        if from_date and int(item["date"][:4]) < int(from_date[:4]):
            continue
        if to_date and int(item["date"][:4]) > int(to_date[:4]):
            continue
        if keyword and keyword.lower() not in item["title"].lower():
            continue
        results.append(item)
    click.echo(json.dumps(results, ensure_ascii=False, indent=2))

# ---------- show コマンド ----------
@cli.command("show")
@click.argument("number")
@click.option("-o", "--output", type=click.Choice(["json", "csv", "md"]), default="md")
def show(number: str, output: str) -> None:
    details = fetch_details(number)
    if output == 'json':
        click.echo(format_json(details))
    elif output == 'csv':
        click.echo(format_csv(details))
    elif output == 'md':
        # Markdown: ヘッダー行 + テーブル
        click.echo(f"# RFC {details['number']}: {details['title']}")
        click.echo()  # 空行
        # 単一レコードをリストに包んで渡す
        click.echo(format_md([details]))
    else:
        raise click.BadParameter(f"unknown output format: {output}")

# ---------- pins コマンド ----------
@cli.command("pin")
@click.argument("number")
def pin(number: str) -> None:
    pins = _load_pins()
    pins.add(number)
    _save_pins(pins)
    click.echo(f"Pinned RFC {number}")

@cli.command("unpin")
@click.argument("number")
def unpin(number: str) -> None:
    pins = _load_pins()
    pins.discard(number)
    _save_pins(pins)
    click.echo(f"Unpinned RFC {number}")

@cli.command("pins")
def pins() -> None:
    click.echo(",".join(sorted(_load_pins())))

if __name__ == "__main__":
    cli()