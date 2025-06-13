import json
from pathlib import Path
import click
from click.testing import CliRunner
from .fetch_rfc import fetch_metadata_list

# ピン情報の保存先
PINS_FILE = Path.home() / ".rfc_chronicle_pins.json"


def load_pins():
    """
    pins.json が存在しない場合は空リストを返し、
    存在する場合は JSON を読み込んでリストを返す
    """
    try:
        data = PINS_FILE.read_text(encoding="utf-8")
        return json.loads(data)
    except FileNotFoundError:
        return []


def save_pins(pins):
    """
    ピンのリストを JSON 形式で保存する
    """
    # 保存先ディレクトリを作成
    PINS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PINS_FILE.write_text(json.dumps(pins, ensure_ascii=False), encoding="utf-8")


@click.group()
def cli():
    """RFC Chronicle CLI"""
    pass


@cli.command()
@click.argument('number', type=int)
def pin(number):
    """RFC をピンに追加"""
    pins = load_pins()
    if number in pins:
        click.echo(f"RFC {number} はすでにピンされています。")
        return

    pins.append(number)
    save_pins(pins)
    click.echo(f"RFC {number} をピンしました。")


@cli.command()
@click.argument('number', type=int)
def unpin(number):
    """RFC のピンを解除"""
    pins = load_pins()
    if number not in pins:
        click.echo(f"RFC {number} はピンされていません。")
        return

    pins.remove(number)
    save_pins(pins)
    click.echo(f"ピンを解除しました: RFC {number}")


@cli.command()
@click.option('--pins-only', is_flag=True, default=False, help='ピンした RFC のみを表示')
def list(pins_only):  # noqa: A002
    """RFC 一覧を取得して表示"""
    items = fetch_metadata_list()
    pins = load_pins() if pins_only else None

    for it in items:
        num = it.number
        title = it.title
        label = f"RFC{num:03d}"

        if pins_only:
            if num not in pins:
                continue

        click.echo(f"{label} {title}")


if __name__ == '__main__':
    cli()
