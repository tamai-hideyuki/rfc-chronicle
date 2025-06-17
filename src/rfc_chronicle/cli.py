import cmd
import textwrap
from pathlib import Path
import click

from .fetch_rfc import RFCClient
from .build_faiss import build_faiss_index
from .fulltext import search_fulltext, rebuild_fulltext_index
from .search import search_metadata, semsearch
from .pin import pin_rfc, unpin_rfc, list_pins
from .formatters import format_json, format_csv, format_md

# インタラクティブシェル用クライアント
client = RFCClient()

class RFCChronicleShell(cmd.Cmd):
    """RFC Chronicle Shell: interactive interface for RFC operations"""
    def __init__(self):
        super().__init__()
        # 標準ヘッダーを無効化
        self.doc_header = None
        self.undoc_header = None

    intro = "Welcome to RFC Chronicle Shell. Type help or ? to list commands.\n"
    prompt = "> "
    # ハイフンを含むコマンド名を許可
    identchars = cmd.Cmd.identchars + '-'

    # クラス属性も無効化
    doc_header = None
    undoc_header = None

    # コマンド一覧と説明
    help_text = {
        "fetch":          "全 RFC メタデータを取得・保存",
        "build-faiss":    "NumPy ベクトルから FAISS インデックスを生成/更新",
        "fulltext":       "SQLite FTS5 で全文検索",
        "index-fulltext": "FTS5 全文検索 DB を再構築",
        "search":         "キャッシュ済みメタデータをキーワードで絞り込み",
        "semsearch":      "FAISS を用いたセマンティック検索",
        "pin":            "RFC をピン留め",
        "pins":           "ピン一覧を表示",
        "show":           "RFC 詳細を表示・エクスポート",
        "unpin":          "ピンを解除",
        "exit":           "シェルを終了",
    }

    def parseline(self, line):
        """ハイフン入りコマンド名を _ に変換"""
        cmd_name, arg, line = super().parseline(line)
        if cmd_name:
            cmd_name = cmd_name.replace('-', '_')
        return cmd_name, arg, line

    def do_help(self, arg):
        """コマンド一覧とヘルプ表示"""
        if arg:
            func = getattr(self, 'do_' + arg.replace('-', '_'), None)
            if func and func.__doc__:
                print(textwrap.dedent(func.__doc__).strip())
            else:
                print(f"No help for '{arg}'")
        else:
            print("Commands:")
            for name, desc in self.help_text.items():
                print(f"  {name:<15} {desc}")
            print()

    def do_fetch(self, arg):
        """全 RFC メタデータを取得・保存"""
        client.fetch_metadata(save=True)

    def do_build_faiss(self, arg):
        """NumPy ベクトルから FAISS インデックスを生成/更新"""
        build_faiss_index()

    def do_fulltext(self, arg):
        """SQLite FTS5 で全文検索"""
        if not arg:
            print("Usage: fulltext <keyword>")
        else:
            for num, snippet in search_fulltext(arg):
                print(f"RFC{num}\t…{snippet.strip()}…")

    def do_index_fulltext(self, arg):
        """FTS5 全文検索 DB を再構築"""
        rebuild_fulltext_index()

    def do_search(self, arg):
        """キャッシュ済みメタデータをキーワードで絞り込み"""
        if not arg:
            print("Usage: search <keyword>")
        else:
            for rfc in search_metadata(arg):
                print(rfc)

    def do_semsearch(self, arg):
        """FAISS を用いたセマンティック検索"""
        if not arg:
            print("Usage: semsearch <keyword>")
        else:
            for score, num in semsearch(arg):
                print(f"RFC{num}: {score}")

    def do_pin(self, arg):
        """RFC をピン留め"""
        pin_rfc(arg)

    def do_unpin(self, arg):
        """ピンを解除"""
        unpin_rfc(arg)

    def do_pins(self, arg):
        """ピン一覧を表示"""
        print(", ".join(list_pins()))

    def do_show(self, arg):
        """RFC 詳細を表示・エクスポート: show <num> [json|csv|md]"""
        if not arg:
            print("Usage: show <number> [json|csv|md]")
            return
        parts = arg.split()
        num = parts[0]
        fmt = parts[1].lower() if len(parts)>1 else 'json'
        save_dir = Path.cwd()/'data'/'texts'
        details = client.fetch_details(num, save_dir)
        records = details if isinstance(details, list) else [details]
        if fmt=='json':
            print(format_json(records))
        elif fmt=='csv':
            print(format_csv(records))
        elif fmt in ('md','markdown'):
            print(format_md(records))
        else:
            print(f"Unknown format: {fmt}")

    def do_exit(self, arg):
        """シェルを終了"""
        return True

@click.group()
def cli():
    """RFC Chronicle CLI"""
    pass

@cli.command('shell')
def shell():
    """Start interactive shell"""
    RFCChronicleShell().cmdloop()

if __name__=='__main__':
    cli()
