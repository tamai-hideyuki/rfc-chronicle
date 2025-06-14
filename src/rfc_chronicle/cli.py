import json
import click
import sqlite3
from pathlib import Path
from typing import Optional, Set, List, Dict, Any
from requests.exceptions import HTTPError
from rfc_chronicle.fetch_rfc import client as rfc_client
from rfc_chronicle.formatters import format_json, format_csv, format_md

from rfc_chronicle.index_fulltext import build_fulltext_db, DB_PATH

DATA_META = Path.cwd() / "data" / "metadata.json"

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
    """全 RFC のメタデータを取得・（オプションで）本文ヘッダ情報とマージして保存"""
    try:
        # 1) メタデータ一覧だけ取得
        meta = rfc_client.fetch_metadata(save=False)
        click.echo(f"Fetched {len(meta)} records.")

        if save:
            # 2) テキストとヘッダを取得しつつ JSON を組み立て
            out_dir = Path("data/texts")
            out_dir.mkdir(parents=True, exist_ok=True)

            enriched: list[dict] = []
            for m in meta:
                num = m.get("number") or m.get("rfc_number")
                try:
                    detail = rfc_client.fetch_details(m, out_dir, use_conditional=False)
                except HTTPError as e:
                    # 404 のみスキップ
                    if e.response.status_code == 404:
                        click.echo(f"RFC{num}: Not Found, skipped")
                        continue
                    # それ以外は止める
                    raise
                enriched.append(detail)

            # 3) ファイルに書き出し
            data_path = Path.cwd() / "data" / "metadata.json"
            data_path.parent.mkdir(parents=True, exist_ok=True)
            data_path.write_text(
                json.dumps(enriched, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            click.echo(f"Saved enriched metadata to {data_path}")

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
    # プロジェクト直下の data/metadata.json を参照
    data_path = Path.cwd() / "data" / "metadata.json"
    if not data_path.exists():
        click.echo("No metadata cache. まずは `fetch --save` を実行してください。", err=True)
        return

    data: List[Dict[str, Any]] = json.loads(data_path.read_text(encoding="utf-8"))
    # 以降、フィルタ処理…
    results = []
    for item in data:
        year = int(item["date"][:4]) if item["date"] else None
        if from_date and (not year or year < from_date):
            continue
        if to_date   and (not year or year > to_date):
            continue
        if keyword and keyword.lower() not in item["title"].lower():
            continue
        results.append(item)

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


@cli.command("index-fulltext")
def index_fulltext():
    """SQLite FTS5 全文検索 DB を再構築します"""
    click.echo(f"Rebuilding fulltext DB at {DB_PATH}…")
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    build_fulltext_db()
    click.echo("Done.")


@cli.command("fulltext")
@click.argument("query", nargs=-1)
@click.option("--limit", "-n", default=20, help="返す件数")
def fulltext(query, limit):
    """
    FTS5 を使った全文検索:
    data/fulltext.db の rfc_text テーブルを検索し
    RFC番号・タイトル・スニペットを表示します
    """
    q = " ".join(query)
    db_path = Path.cwd() / "data" / "fulltext.db"
    conn = sqlite3.connect(db_path)
    sql = f"""
      SELECT number, title,
             snippet(rfc_text, '[…]', '[…]', '…', 10, 3) AS excerpt
      FROM rfc_text
      WHERE rfc_text MATCH ?
      LIMIT {limit};
    """
    for num, title, excerpt in conn.execute(sql, (q,)):
        click.echo(f"RFC{num}\t{title}")
        click.echo(f"  …{excerpt}…\n")
    conn.close()


if __name__ == "__main__":
    cli()
