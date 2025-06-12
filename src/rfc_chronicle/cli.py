import click
from datetime import datetime
from typing import Optional, List

from .search import filter_rfcs
from .fetch_rfc import load_all_rfcs  # Assumes this function loads all RFC metadata


def parse_date(date_str: Optional[str]) -> Optional[datetime.date]:
    """
    YYYY-MM-DD形式の文字列をdateオブジェクトに変換。
    Noneまたは空文字の場合はNoneを返す。
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError as e:
        raise click.UsageError(f"Invalid date format: {date_str}. Use YYYY-MM-DD.")

@click.command()
@click.option(
    '--status', '-s',
    help='フィルタ対象のステータスをカンマ区切りで指定 (例: draft,active)',
    default=None
)
@click.option(
    '--from', 'date_from',
    help='開始日 (YYYY-MM-DD)',
    default=None
)
@click.option(
    '--to', 'date_to',
    help='終了日 (YYYY-MM-DD)',
    default=None
)
@click.option(
    '--keyword', '-k',
    help='タイトルやabstractなどに含まれるキーワードでフィルタ',
    default=None
)
def fetch(status: Optional[str], date_from: Optional[str], date_to: Optional[str], keyword: Optional[str]):
    """
    RFCメタデータを指定条件でフィルタリングして一覧表示するコマンド。
    """
    # ステータスのパース: カンマ区切り
    statuses: Optional[List[str]] = None
    if status:
        statuses = [s.strip() for s in status.split(',') if s.strip()]

    # 日付のパース
    dt_from = parse_date(date_from)
    dt_to = parse_date(date_to)

    # RFCメタデータ読み込み
    all_rfcs = load_all_rfcs()

    # フィルタ適用
    filtered = filter_rfcs(
        all_rfcs,
        statuses=statuses,
        date_from=dt_from,
        date_to=dt_to,
        keyword=keyword
    )

    # 結果出力
    if not filtered:
        click.echo('No RFCs match the given criteria.')
        return

    for r in filtered:
        click.echo(f"{r.id}\t{r.title}\t{r.status}\t{r.date}")

if __name__ == '__main__':
    fetch()
