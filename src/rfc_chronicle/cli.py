import json
import re
import click
import sqlite3
import faiss
import numpy as np

from pathlib import Path
from typing import Optional, Set, List, Dict, Any
from requests.exceptions import HTTPError

from rfc_chronicle.fetch_rfc import client as rfc_client
from rfc_chronicle.formatters import format_json, format_csv, format_md
from rfc_chronicle.index_fulltext import build_fulltext_db, DB_PATH

from scripts.build_faiss_index import (
    build_flat_index,
    build_ivf_index,
    build_hnsw_index,
    load_vectors,
    save_index,
)

# プロジェクト直下の metadata.json
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
    pass


@cli.command()
@click.option('-s', '--save', is_flag=True, help="ローカルにメタデータを保存")
def fetch(save: bool) -> None:
    """全 RFC のメタデータを取得・（オプションで）本文ヘッダ情報とマージして保存"""
    try:
        meta_list = rfc_client.fetch_metadata(save=False)
        click.echo(f"Fetched {len(meta_list)} records.")

        if save:
            texts_dir = Path("data/texts")
            texts_dir.mkdir(parents=True, exist_ok=True)

            enriched: List[Dict[str, Any]] = []
            for m in meta_list:
                num = m.get("number") or m.get("rfc_number")
                try:
                    detail = rfc_client.fetch_details(m, texts_dir, use_conditional=False)
                except HTTPError as e:
                    if e.response.status_code == 404:
                        click.echo(f"RFC{num}: Not Found, skipped")
                        continue
                    raise
                enriched.append(detail)

            DATA_META.parent.mkdir(parents=True, exist_ok=True)
            DATA_META.write_text(
                json.dumps(enriched, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            click.echo(f"Saved enriched metadata to {DATA_META}")
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
    if not DATA_META.exists():
        click.echo("No metadata cache. まずは `fetch --save` を実行してください。", err=True)
        return

    data = json.loads(DATA_META.read_text(encoding="utf-8"))
    results = []

    for item in data:
        year = None
        date_str = item.get("date", "")
        if date_str:
            m = re.search(r"\b(\d{4})\b", date_str)
            if m:
                year = int(m.group(1))

        if from_date and (year is None or year < from_date):
            continue
        if to_date   and (year is None or year > to_date):
            continue
        if keyword and keyword.lower() not in item.get("title", "").lower():
            continue

        results.append(item)

    click.echo(json.dumps(results, ensure_ascii=False, indent=2))


@cli.command()
@click.argument('number', type=int)
@click.option('-o', '--output', type=click.Choice(['json','csv','md']), default='md')
def show(number: int, output: str) -> None:
    """指定RFCの詳細（メタデータ＋本文）を表示"""
    try:
        meta_list = rfc_client.fetch_metadata(save=False)
        meta = next(
            m for m in meta_list
            if rfc_client._normalize_number(m["number"]) == number
        )

        texts_dir = Path("data/texts")
        texts_dir.mkdir(parents=True, exist_ok=True)
        details = rfc_client.fetch_details(meta, texts_dir, use_conditional=False)
    except StopIteration:
        click.echo(f"RFC {number} が見つかりません", err=True)
        return
    except Exception as e:
        click.echo(str(e), err=True)
        return

    if output == 'json':
        click.echo(format_json(details))
    elif output == 'csv':
        click.echo(format_csv(details))
    else:
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
def index_fulltext() -> None:
    """SQLite FTS5 全文検索 DB を再構築します"""
    click.echo(f"Rebuilding fulltext DB at {DB_PATH}…")
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    build_fulltext_db()
    click.echo("Done.")


@cli.command("fulltext")
@click.argument("query", nargs=-1)
@click.option("--limit", "-n", default=20, help="返す件数")
def fulltext(query: List[str], limit: int) -> None:
    """
    FTS5 を使った全文検索:
    data/fulltext.db の rfc_text テーブルを検索し
    RFC番号・タイトル・スニペットを表示します
    """
    q = " ".join(query)
    db_path = Path.cwd() / "data" / "fulltext.db"
    conn = sqlite3.connect(db_path)
    sql = """
      SELECT number, title,
             snippet(rfc_text, '[…]', '[…]', '…', 10, 3) AS excerpt
      FROM rfc_text
      WHERE rfc_text MATCH ?
      LIMIT ?;
    """
    for num, title, excerpt in conn.execute(sql, (q, limit)):
        click.echo(f"RFC{num}\t{title}")
        click.echo(f"  …{excerpt}…\n")
    conn.close()


@cli.command("build-faiss")
@click.option(
    "--vectors", "-v",
    default="data/vectors.npy",
    type=click.Path(exists=True, dir_okay=False),
    help="読み込むベクトルの .npy ファイルパス"
)
@click.option(
    "--index", "-i",
    default="data/faiss_index.bin",
    type=click.Path(dir_okay=False),
    help="保存する FAISS インデックスファイルのパス"
)
@click.option(
    "--update", "-u",
    is_flag=True,
    help="既存インデックスを読み込み、新規ベクトルを追加"
)
@click.option(
    "--type", "-t",
    type=click.Choice(["flat", "ivf", "hnsw"], case_sensitive=False),
    default="flat",
    help="生成するインデックスタイプ (flat, ivf, hnsw)"
)
def build_faiss(vectors, index, update, type):
    """
    NumPy ベクトルから FAISS インデックスを生成・更新する。
    """
    vectors_path = Path(vectors)
    index_path = Path(index)
    vecs = load_vectors(vectors_path)

    if update:
        if not index_path.exists():
            click.echo(f"既存インデックスが見つかりません ({index_path})。Flat で新規作成します。")
            idx = build_flat_index(vecs)
        else:
            idx = faiss.read_index(str(index_path))
            idx.add(vecs)
        save_index(idx, index_path)
        return

    # 全量ビルド
    if type == "flat":
        idx = build_flat_index(vecs)
    elif type == "ivf":
        idx = build_ivf_index(vecs)
    elif type == "hnsw":
        idx = build_hnsw_index(vecs)
    save_index(idx, index_path)


if __name__ == "__main__":
    cli()
