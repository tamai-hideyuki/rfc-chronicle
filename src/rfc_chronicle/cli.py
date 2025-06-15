"""
RFC-Chronicle ─ CLI エントリポイント
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import click
import faiss
import numpy as np
from requests.exceptions import HTTPError

# ─────────────────────────────────────────────── import RFC-Chronicle internals
from rfc_chronicle.fetch_rfc import client as rfc_client
from rfc_chronicle.formatters import format_csv, format_json, format_md
from rfc_chronicle.index_fulltext import DB_PATH, build_fulltext_db
from rfc_chronicle.search import semsearch

from scripts.build_faiss_index import (
    build_flat_index,
    build_hnsw_index,
    build_ivf_index,
    load_vectors,
    save_index,
)

# ─────────────────────────────────────────────── constants / globals
DATA_META: Path = Path.cwd() / "data" / "metadata.json"
PINS_FILE: Optional[Path] = None  # tests で差し替え可


# ═══════════════════════════════════════════════ helper ─ pins
def _load_pins() -> Set[str]:
    if not PINS_FILE or not PINS_FILE.exists():
        return set()
    return set(json.loads(PINS_FILE.read_text(encoding="utf-8")))


def _save_pins(pins: Set[str]) -> None:
    if not PINS_FILE:
        return
    PINS_FILE.write_text(json.dumps(sorted(pins), ensure_ascii=False), encoding="utf-8")


# ═══════════════════════════════════════════════ root group
@click.group()
def cli() -> None:
    """RFC-Chronicle CLI"""
    pass


# ═══════════════════════════════════════════════ semsearch
@cli.command("semsearch")
@click.argument("query")
@click.option("--topk", default=10, show_default=True, help="返す上位件数")
def semsearch_cli(query: str, topk: int) -> None:
    """FAISS ベクトル検索（セマンティック検索）"""
    for num, dist in semsearch(query, topk):
        click.echo(f"RFC{num}\t{dist:.4f}")


# ═══════════════════════════════════════════════ fetch
@cli.command()
@click.option("-s", "--save", is_flag=True, help="ローカルにメタデータを保存")
def fetch(save: bool) -> None:
    """全 RFC のメタデータを取得し、必要なら本文ヘッダとマージして保存"""
    try:
        meta_list = rfc_client.fetch_metadata(save=False)
        click.echo(f"Fetched {len(meta_list)} records.")

        if not save:
            return

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
        DATA_META.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")
        click.echo(f"Saved enriched metadata to {DATA_META}")
    except Exception as exc:  # pragma: no cover
        click.echo(f"Error fetching metadata: {exc}", err=True)


# ═══════════════════════════════════════════════ search (metadata filter)
@cli.command()
@click.option("--from-date", type=int, help="発行年 FROM (YYYY)")
@click.option("--to-date", type=int, help="発行年 TO   (YYYY)")
@click.option("--keyword", type=str, help="タイトルに含むキーワード")
def search(from_date: int | None, to_date: int | None, keyword: str | None) -> None:
    """キャッシュ済みメタデータを条件で絞り込み"""
    if not DATA_META.exists():
        click.echo("No metadata cache. まずは `fetch --save` を実行してください。", err=True)
        return

    data = json.loads(DATA_META.read_text(encoding="utf-8"))
    results: List[Dict[str, Any]] = []

    for item in data:
        year: int | None = None
        if m := re.search(r"\b(\d{4})\b", item.get("date", "")):
            year = int(m.group(1))

        if from_date and (year is None or year < from_date):
            continue
        if to_date and (year is None or year > to_date):
            continue
        if keyword and keyword.lower() not in item.get("title", "").lower():
            continue

        results.append(item)

    click.echo(json.dumps(results, ensure_ascii=False, indent=2))


# ═══════════════════════════════════════════════ show
@cli.command()
@click.argument("number", type=int)
@click.option(
    "-o",
    "--output",
    type=click.Choice(["json", "csv", "md"]),
    default="md",
    show_default=True,
)
def show(number: int, output: str) -> None:
    """指定 RFC の詳細を表示・エクスポート"""
    try:
        meta = next(
            m
            for m in rfc_client.fetch_metadata(save=False)
            if rfc_client._normalize_number(m["number"]) == number
        )

        texts_dir = Path("data/texts")
        texts_dir.mkdir(parents=True, exist_ok=True)
        detail = rfc_client.fetch_details(meta, texts_dir, use_conditional=False)
    except StopIteration:
        click.echo(f"RFC {number} が見つかりません", err=True)
        return
    except Exception as exc:  # pragma: no cover
        click.echo(str(exc), err=True)
        return

    if output == "json":
        click.echo(format_json(detail))
    elif output == "csv":
        click.echo(format_csv(detail))
    else:
        click.echo(f"# RFC {detail['number']}: {detail['title']}\n")
        click.echo(format_md([detail]))


# ═══════════════════════════════════════════════ pin / unpin / pins
@cli.command()
@click.argument("number")
def pin(number: str) -> None:
    """RFC 番号をピン留め"""
    pins = _load_pins()
    if number in pins:
        click.echo(f"RFC {number} is already pinned.", err=True)
        return
    pins.add(number)
    _save_pins(pins)
    click.echo(f"Pinned RFC {number}")


@cli.command()
@click.argument("number")
def unpin(number: str) -> None:
    """ピンを解除"""
    pins = _load_pins()
    if number not in pins:
        click.echo(f"RFC {number} is not pinned.", err=True)
        return
    pins.remove(number)
    _save_pins(pins)
    click.echo(f"Unpinned RFC {number}")


@cli.command("pins")
def list_pins() -> None:
    """ピン一覧を表示"""
    pins = sorted(_load_pins())
    click.echo("\n".join(pins) if pins else "No pinned RFCs.")


# ═══════════════════════════════════════════════ full-text index
@cli.command("index-fulltext")
def index_fulltext() -> None:
    """SQLite FTS5 全文検索 DB を再構築"""
    click.echo(f"Rebuilding fulltext DB at {DB_PATH} …")
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    build_fulltext_db()
    click.echo("Done.")


@cli.command("fulltext")
@click.argument("query", nargs=-1)
@click.option("--limit", "-n", default=20, show_default=True, help="返す件数")
def fulltext(query: List[str], limit: int) -> None:
    """
    SQLite FTS5 を使った全文検索
    RFC 番号・タイトル・抜粋を表示
    """
    q = " ".join(query)
    conn = sqlite3.connect(Path.cwd() / "data" / "fulltext.db")
    sql = """
        SELECT number,
               title,
               snippet(rfc_text, '[…]', '[…]', '…', 10, 3) AS excerpt
        FROM   rfc_text
        WHERE  rfc_text MATCH ?
        LIMIT  ?;
    """
    for num, title, excerpt in conn.execute(sql, (q, limit)):
        click.echo(f"RFC{num}\t{title}")
        click.echo(f"  …{excerpt}…\n")
    conn.close()


# ═══════════════════════════════════════════════ build-faiss
@cli.command("build-faiss")
@click.option(
    "--vectors",
    "-v",
    default="data/vectors.npy",
    type=click.Path(exists=True, dir_okay=False),
    show_default=True,
    help="入力ベクトル (.npy)",
)
@click.option(
    "--index",
    "-i",
    default="data/faiss_index.bin",
    type=click.Path(dir_okay=False),
    show_default=True,
    help="出力インデックス (.bin)",
)
@click.option("--update", "-u", is_flag=True, help="既存インデックスへ追加登録")
@click.option(
    "--type",
    "-t",
    type=click.Choice(["flat", "ivf", "hnsw"]),
    default="flat",
    show_default=True,
    help="インデックスタイプ",
)
def build_faiss(vectors: str, index: str, update: bool, type: str) -> None:
    """NumPy ベクトルから FAISS インデックスを生成 / 更新"""
    vecs = load_vectors(Path(vectors))
    index_path = Path(index)

    if update and index_path.exists():
        idx = faiss.read_index(str(index_path))
        idx.add(vecs)
        save_index(idx, index_path)
        click.echo("Index updated.")
        return
    if update and not index_path.exists():
        click.echo("既存インデックスが無いので新規作成します。")

    if type == "flat":
        idx = build_flat_index(vecs)
    elif type == "ivf":
        idx = build_ivf_index(vecs)
    else:  # hnsw
        idx = build_hnsw_index(vecs)

    save_index(idx, index_path)
    click.echo(f"Index saved → {index_path}")


# ═══════════════════════════════════════════════ entrypoint
if __name__ == "__main__":  # pragma: no cover
    cli()
