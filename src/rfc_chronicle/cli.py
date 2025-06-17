import cmd
import click

from .fetch_rfc import RFCClient
from .build_faiss import build_faiss_index
from .fulltext import search_fulltext as fulltext_search, rebuild_fulltext_index
from .search import search_metadata, semsearch as semantic_search
from .pin import pin_rfc, unpin_rfc, list_pins

from rfc_chronicle.fulltext import search_fulltext
from rfc_chronicle.formatters import format_json, format_csv, format_md



# インタラクティブシェル用のクライアントインスタンス
client = RFCClient()

class RFCChronicleShell(cmd.Cmd):
    intro = "Welcome to RFC Chronicle Shell. Type help or ? to list commands.\n"
    prompt = "> "

    def do_fetch(self, arg):
        """Fetch all RFC metadata and store"""
        client.fetch_metadata(save=True)

    def do_build_faiss(self, arg):
        """Build or update FAISS index"""
        build_faiss_index()

    def do_fulltext(self, arg):
        """Fulltext search: fulltext <keyword>"""
        if not arg:
            print("Usage: fulltext <keyword>")
        else:
            results = fulltext_search(arg)
            for r in results:
                print(r)

    def do_index_fulltext(self, arg):
        """Rebuild FTS5 fulltext index"""
        rebuild_fulltext_index()

    def do_search(self, arg):
        """Search metadata: search <query>"""
        if not arg:
            print("Usage: search <query>")
        else:
            results = search_metadata(arg)
            for r in results:
                print(r)

    def do_semsearch(self, arg):
        """Semantic search: semsearch <query>"""
        if not arg:
            print("Usage: semsearch <query>")
        else:
            results = semantic_search(arg)
            for score, num in results:
                print(f"RFC{num}: {score}")

    def do_pin(self, arg):
        """Pin RFC: pin <number>"""
        pin_rfc(arg)

    def do_unpin(self, arg):
        """Unpin RFC: unpin <number>"""
        unpin_rfc(arg)

    def do_pins(self, arg):
        """Show pinned RFCs"""
        pins = list_pins()
        print("Pinned RFCs:", ", ".join(pins))

    def do_show(self, arg):
        """Show details or export: show <number> [--format=md|json|csv]"""
        if not arg:
            print("Usage: show <number>")
        else:
            show_details(arg)

    def do_exit(self, arg):
        """Exit the shell"""
        print("Bye!")
        return True

# CLI Entry Point
@click.group()
def cli():
    "RFC Chronicle CLI"
    pass

@cli.command("shell")
def shell():
    "Start interactive shell"
    RFCChronicleShell().cmdloop()


@cli.command("fulltext")
@click.argument("query", nargs=1)
@click.option("-l", "--limit", default=10, show_default=True,
              help="取得する結果の最大件数")
def fulltext_cmd(query: str, limit: int):
    """すべての RFC 本文を対象に QUERY で全文検索します。"""
    results = search_fulltext(query, limit)
    if not results:
        click.echo("結果が見つかりませんでした。")
        return
    for rfc_num, snippet in results:
        click.echo(f"RFC{rfc_num}\t…{snippet.strip()}…")


@cli.command("show")
@click.argument("number", nargs=1)
@click.option(
    "-o", "--output",
    type=click.Choice(["json", "csv", "md"], case_sensitive=False),
    default="json", show_default=True,
    help="表示フォーマットを選択します（json, csv, md）"
)
def show_cmd(number: str, output: str):
    """
    指定した RFC 番号のメタデータ＆本文の詳細を取得して表示します。
    """
    from pathlib import Path

    # 保存先ディレクトリ
    save_dir = Path.cwd() / "data" / "texts"

    # RFC の詳細を取得
    details = client.fetch_details(number, save_dir)

    # 単一レコードの場合でもリスト化してフォーマッタへ渡す
    records = details if isinstance(details, list) else [details]

    # 出力
    if output.lower() == "json":
        click.echo(format_json(records))
    elif output.lower() == "csv":
        click.echo(format_csv(records))
    elif output.lower() == "md":
        click.echo(format_md(records))


if __name__ == "__main__":
    cli()
