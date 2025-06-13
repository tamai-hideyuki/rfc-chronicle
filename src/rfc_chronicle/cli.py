import json
from pathlib import Path
import click
from filelock import FileLock

# （既存のコード…）
# fetch_metadata_list のスタブ
try:
    from rfc_chronicle.fetch_rfc import fetch_metadata_list
except ImportError:
    def fetch_metadata_list(*args, **kwargs):
        return []

# デフォルトピンファイルパス
PINS_FILE = Path(".rfc_data/pins.json")
LOCK_SUFFIX = ".lock"

def ensure_data_dir(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

def load_pins(path: Path = PINS_FILE) -> list[int]:
    ensure_data_dir(path)
    if not path.exists():
        save_pins([], path)
    lock = FileLock(str(path) + LOCK_SUFFIX)
    with lock:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return [int(r) for r in data]
        except json.JSONDecodeError:
            backup = path.with_suffix(path.suffix + ".bak")
            path.rename(backup)
            save_pins([], path)
            return []

def save_pins(pins: list[int], path: Path = PINS_FILE) -> None:
    ensure_data_dir(path)
    lock = FileLock(str(path) + LOCK_SUFFIX)
    with lock:
        path.write_text(json.dumps(pins, indent=2, ensure_ascii=False), encoding="utf-8")


@click.group()
def cli():
    """RFC-chronicle CLI"""
    pass

@cli.command()
@click.argument('rfc', type=int)
def fetch(rfc: int):
    """Fetch RFC metadata by number"""
    try:
        from rfc_chronicle.fetch_rfc import fetch_metadata
    except ImportError:
        click.echo(f"Error: fetch_metadata not available")
        return
    meta = fetch_metadata(rfc)
    # 出力フォーマットはあとで調整
    click.echo(meta)


@cli.command()
@click.argument('rfc', type=int)
def pin(rfc: int):
    pins = load_pins()
    if rfc in pins:
        click.echo(f"RFC {rfc} はすでにピンされています。")
        return
    pins.append(rfc)
    save_pins(pins)
    click.echo(f"RFC {rfc} をピンしました。📌")

@cli.command()
@click.argument('rfc', type=int)
def unpin(rfc: int):
    pins = load_pins()
    if rfc not in pins:
        click.echo(f"RFC {rfc} はピンされていません。")
        return
    pins.remove(rfc)
    save_pins(pins)
    click.echo(f"RFC {rfc} のピンを解除しました。❌")

@cli.command(name='list')
@click.option('--pins-only', is_flag=True, help='ピン済みのみ表示')
@click.option('--show-pins', is_flag=True, help='全RFC表示にピンマークを付与')
@click.argument('other_args', nargs=-1)
def list_rfc(pins_only: bool, show_pins: bool, other_args):
    pins = load_pins()
    all_items = fetch_metadata_list(*other_args)

    def format_item(item):
        mark = '📌' if item.number in pins else '   '
        return f"{mark} RFC{item.number:03d}  {item.title}"

    filtered = all_items if not pins_only else [i for i in all_items if i.number in pins]
    sorted_items = sorted(filtered, key=lambda i: (i.number not in pins, i.number))

    for item in sorted_items:
        if show_pins or pins_only:
            click.echo(format_item(item))
        else:
            click.echo(item.summary_line())
