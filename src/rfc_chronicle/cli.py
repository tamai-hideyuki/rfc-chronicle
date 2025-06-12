import click
from datetime import datetime

@click.group()
def cli():
    """rfc-chronicle: CLI for managing RFC knowledge"""
    pass

@cli.command()
def fetch():
    """RFC-Editor から最新メタデータを取得してキャッシュ"""
    click.echo("[INFO] Fetching RFC metadata...")
    # モックを確実に反映させるため、コマンド実行時にインポート
    from rfc_chronicle.fetch_rfc import fetch_metadata
    from rfc_chronicle.utils    import META_FILE

    data = fetch_metadata(save=True)
    click.echo(f"[INFO] Saved {len(data)} RFC entries to {META_FILE}")

@cli.command()
@click.option("--status", help="Filter by RFC status")
@click.option("--from-date", "from_date", help="Filter from date YYYY or 'Month YYYY'")
@click.option("--to-date", "to_date", help="Filter to date YYYY or 'Month YYYY'")
@click.option("--keyword", help="Keyword to search in title")
def search(status, from_date, to_date, keyword):
    """ローカルキャッシュから RFC を検索"""
    # モックを確実に反映させるため、コマンド実行時にインポート
    from rfc_chronicle.utils import META_FILE, read_json
    data = read_json(META_FILE) or []
    click.echo(f"[DEBUG] Loaded {len(data)} RFC entries from cache")

    # 日付パース関数
    def parse_date(ds: str, is_to=False):
        if not ds:
            return None
        try:
            return datetime.strptime(ds, "%B %Y")
        except ValueError:
            pass
        try:
            dt = datetime.strptime(ds, "%Y")
            if is_to:
                return dt.replace(month=12, day=31)
            return dt
        except ValueError:
            click.echo(f"[WARN] Invalid date format: '{ds}'")
            return None

    dt_from = parse_date(from_date)
    dt_to = parse_date(to_date, is_to=True)
    click.echo(f"[DEBUG] Applying filters - status={status!r}, from={dt_from}, to={dt_to}, keyword={keyword!r}")

    results = []
    for item in data:
        date_str = item.get("date", "")
        try:
            dt_item = datetime.strptime(date_str, "%B %Y")
        except ValueError:
            click.echo(f"[WARN] Skipping unparseable date: {date_str}")
            continue
        status_match = not status or item.get("status") == status
        from_match = not dt_from or dt_item >= dt_from
        to_match = not dt_to or dt_item <= dt_to
        keyword_match = not keyword or keyword.lower() in item.get("title", "").lower()

        click.echo(
            f"[DEBUG] Checking RFC {item['number']}: dt_item={dt_item.date()}, "
            f"status_match={status_match}, from_match={from_match}, "
            f"to_match={to_match}, keyword_match={keyword_match}"
        )
        if status_match and from_match and to_match and keyword_match:
            click.echo(f"[INFO] Matched RFC {item['number']}")
            results.append(item)
        else:
            click.echo(f"[INFO] Excluded RFC {item['number']}")

    click.echo(f"[DEBUG] {len(results)} entries matched filters")
    if not results:
        click.echo("No RFCs found.")
        return
    for r in results:
        click.echo(f"RFC {r['number']}: {r['title']} ({r['date']}, {r['status']})")

@cli.command()
@click.argument("rfc_number")
def pin(rfc_number):
    """指定した RFC 番号をピン留め"""
    from rfc_chronicle.utils import PINS_FILE, read_json, write_json
    pins = read_json(PINS_FILE) or []
    if rfc_number in pins:
        click.echo(f"RFC {rfc_number} is already pinned.")
        return
    pins.append(rfc_number)
    write_json(PINS_FILE, pins)
    click.echo(f"Pinned RFC {rfc_number}.")

@cli.command(name="list-pins")
def list_pins():
    """ピン留めした RFC を一覧表示"""
    from rfc_chronicle.utils import PINS_FILE, read_json
    pins = read_json(PINS_FILE) or []
    if not pins:
        click.echo("No pinned RFCs.")
        return
    click.echo("Pinned RFCs:")
    for num in pins:
        click.echo(f"- RFC {num}")

@cli.command()
@click.argument("rfc_number")
def unpin(rfc_number):
    """指定した RFC 番号のピンを解除"""
    from rfc_chronicle.utils import PINS_FILE, read_json, write_json
    pins = read_json(PINS_FILE) or []
    if rfc_number not in pins:
        click.echo(f"RFC {rfc_number} is not pinned.")
        return
    pins.remove(rfc_number)
    write_json(PINS_FILE, pins)
    click.echo(f"Unpinned RFC {rfc_number}.")

if __name__ == "__main__":
    cli()
