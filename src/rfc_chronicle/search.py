# src/rfc_chronicle/search.py
import click
from .utils import read_json, META_FILE

@cli.command()
@click.option("--status", help="Filter by RFC status")
@click.option("--from-date", "from_date", help="Filter from date YYYY-MM-DD")
@click.option("--to-date", "to_date", help="Filter to date YYYY-MM-DD")
@click.option("--keyword", help="Keyword to search in title")
def search(status, from_date, to_date, keyword):
    """ローカルキャッシュから RFC を検索"""
    data = read_json(META_FILE) or []
    filtered = []
    for item in data:
        if status and item["status"] != status:
            continue
        if from_date and item["date"] < from_date:
            continue
        if to_date and item["date"] > to_date:
            continue
        if keyword and keyword.lower() not in item["title"].lower():
            continue
        filtered.append(item)

    if not filtered:
        click.echo("No RFCs found.")
        return

    for r in filtered:
        click.echo(f'RFC {r["number"]}: {r["title"]} ({r["date"]}, {r["status"]})')
