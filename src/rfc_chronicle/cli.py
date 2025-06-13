import json
from pathlib import Path
import click
from .fetch_rfc import fetch_metadata_list

# ピン情報の保存先
PINS_FILE = Path.home() / ".rfc_chronicle_pins.json"

def load_pins():
    """
    pins.json が存在しない場合は空リストを返し、
    ファイルを作成する。存在する場合は JSON を読み込んでリストを返す
    """
    if not PINS_FILE.exists():
        # ディレクトリを作成し、空リストを書き出す
        PINS_FILE.parent.mkdir(parents=True, exist_ok=True)
        PINS_FILE.write_text(json.dumps([], ensure_ascii=False), encoding="utf-8")
        return []
    data = PINS_FILE.read_text(encoding="utf-8")
    return json.loads(data)


def save_pins(pins):
    """
    ピンのリストを JSON 形式で保存する
    """
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

@cli.command('list')
@click.option('--pins-only', is_flag=True, default=False, help='ピンした RFC のみを表示')
@click.option('--show-pins', is_flag=True, default=False, help='ピン済みをマークして表示')
def list_cmd(pins_only, show_pins):  # noqa: A002
    """RFC 一覧を取得して表示"""
    items = fetch_metadata_list()
    pins = load_pins() if (pins_only or show_pins) else []

    for it in items:
        num = it.number
        title = it.title
        if pins_only and num not in pins:
            continue

        label = f"RFC{num:03d} {title}"
        if show_pins:
            # pinned: show 📌, else indent with spaces
            prefix = "📌 " if num in pins else "   "
            click.echo(f"{prefix}{label}")
        else:
            click.echo(label)


@cli.command('show')
@click.argument('number', type=int)
@click.option('-o', '--output', type=click.Choice(['json','csv','md']), default='md', help='出力フォーマット')
def show(number, output):
    """RFC の詳細を表示し、エクスポートします"""
    details = fetch_details(number)
    if output == 'json':
        click.echo(format_json(details))
    elif output == 'csv':
        click.echo(format_csv(details))
    else:
        click.echo(format_md(details))


if __name__ == '__main__':
    cli()
