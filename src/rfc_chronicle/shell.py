import cmd
import click
from .fetch_rfc import RFCClient
from .build_faiss import build_faiss_index
from .fulltext import fulltext_search, rebuild_fulltext_index
from .search import search_metadata, semantic_search
from .pin import pin_rfc, unpin_rfc, list_pins
from .show import show_details

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

if __name__ == "__main__":
    cli()
