import cmd
import textwrap
from pathlib import Path
import click

from .fetch_rfc import RFCClient
from .build_faiss import build_faiss_index

from .fulltext import search_fulltext as fulltext_search, rebuild_fulltext_index
from .search import search_metadata, semsearch as semantic_search
from .pin import pin_rfc, unpin_rfc, list_pins
from .show import show_details

# インタラクティブシェル用のクライアントインスタンス
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

    # クラス属性としても無効化
    doc_header = None
    undoc_header = None

    # コマンド一覧と日本語説明
    help_text = {
        "build-faiss":    "NumPy ベクトルから FAISS インデックスを生成 / 更新",
        "fetch":          "全 RFC のメタデータを取得し、必要なら本文ヘッダとマージして保存",
        "fulltext":       "SQLite FTS5 を使った全文検索",
        "index-fulltext": "SQLite FTS5 全文検索 DB を再構築",
        "pin":            "RFC 番号をピン留め",
        "pins":           "ピン一覧を表示",
        "search":         "キャッシュ済みメタデータを条件で絞り込み",
        "semsearch":      "FAISS ベクトル検索（セマンティック検索）",
        "show":           "指定 RFC の詳細を表示・エクスポート",
        "unpin":          "ピンを解除",
        "exit":           "シェルを終了",
    }

    def parseline(self, line):
        """ハイフン入りコマンド名をメソッド名に合わせて変換"""
        cmd_name, arg, line = super().parseline(line)
        if cmd_name:
            cmd_name = cmd_name.replace('-', '_')
        return cmd_name, arg, line

    def do_help(self, arg):
        """コマンド一覧とヘルプを表示"""
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
        """全 RFC のメタデータを取得し、必要なら本文ヘッダとマージして保存"""
        client.fetch_metadata(save=True)

    def do_build_faiss(self, arg):
        """NumPy ベクトルから FAISS インデックスを生成 / 更新"""
        build_faiss_index()

    def do_fulltext(self, arg):
        """SQLite FTS5 を使った全文検索"""
        if not arg:
            print("Usage: fulltext <keyword>")
        else:
            for num, snippet in fulltext_search(arg):
                print(f"RFC{num}\t…{snippet.strip()}…")

    def do_index_fulltext(self, arg):
        """SQLite FTS5 全文検索 DB を再構築"""
        rebuild_fulltext_index()

    def do_search(self, arg):
        """キャッシュ済みメタデータを条件で絞り込み"""
        if not arg:
            print("Usage: search <query>")
        else:
            for entry in search_metadata(arg):
                print(entry)

    def do_semsearch(self, arg):
        """FAISS ベクトル検索（セマンティック検索）"""
        if not arg:
            print("Usage: semsearch <query>")
        else:
            for score, num in semantic_search(arg):
                print(f"RFC{num}: {score}")

    def do_pin(self, arg):
        """RFC 番号をピン留め"""
        pin_rfc(arg)

    def do_unpin(self, arg):
        """ピンを解除"""
        unpin_rfc(arg)

    def do_pins(self, arg):
        """ピン一覧を表示"""
        pins = list_pins()
        print("Pinned RFCs:", ", ".join(pins))

    def do_show(self, arg):
        """指定 RFC の詳細を表示・エクスポート"""
        if not arg:
            print("Usage: show <number> [--format=md|json|csv]")
        else:
            show_details(arg)

    def do_exit(self, arg):
        """シェルを終了"""
        print("Bye!")
        return True

@click.group()
def cli():
    """RFC Chronicle CLI"""
    pass

@cli.command('shell')
def shell():
    """Start interactive shell"""
    RFCChronicleShell().cmdloop()

if __name__ == '__main__':
    cli()
