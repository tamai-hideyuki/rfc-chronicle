import cmd
import textwrap
from pathlib import Path
from importlib.metadata import version

import click
import numpy as np
import faiss

from rfc_chronicle.fetch_rfc import RFCClient
from rfc_chronicle.search import search_metadata, semsearch
from rfc_chronicle.fulltext import search_fulltext, rebuild_fulltext_index
from rfc_chronicle.build_faiss import build_faiss_index
from rfc_chronicle.pin import pin_rfc, unpin_rfc, list_pins
from rfc_chronicle.show import show_rfc_details
from rfc_chronicle.formatters import format_json, format_csv, format_md

# ---------------------------------------------------------------------------
# CLI entry point & interactive shell
# ---------------------------------------------------------------------------
__version__ = version("rfc-chronicle")

client = RFCClient()  # shared client instance for the shell


class RFCChronicleShell(cmd.Cmd):
    """RFC Chronicle – interactive shell."""

    intro = (
        "Welcome to RFC Chronicle Shell. Type 'help' or '?' to list commands.\n"
        "Tip: Use hyphens (e.g. build-faiss) just like the CLI commands."
    )
    prompt = "> "
    identchars = cmd.Cmd.identchars + "-"  # allow hyphens in command names

    # Simplified help mapping (command -> description)
    _HELP = {
        "fetch":          "Fetch and cache all RFC metadata",
        "build-faiss":    "(Re)build FAISS index from vectors",
        "fulltext":       "Full‑text search in cached documents",
        "index-fulltext": "Rebuild the SQLite FTS5 index",
        "search":         "Keyword search in cached metadata",
        "semsearch":      "Semantic search via FAISS",
        "pin":            "Pin an RFC number for later",
        "pins":           "List pinned RFC numbers",
        "show":           "Show / export RFC details",
        "unpin":          "Unpin an RFC number",
        "exit":           "Exit the shell",
    }

    # ------------------------------------------------------------------ utils
    def parseline(self, line):
        """Allow hyphenated commands by converting '-' -> '_' for method lookup."""
        cmd_name, arg, line = super().parseline(line)
        if cmd_name:
            cmd_name = cmd_name.replace("-", "_")
        return cmd_name, arg, line

    def do_help(self, arg):  # noqa: N802  (cmd.Stdlib naming style)
        """Show help for individual command or list all commands."""
        if arg:
            func = getattr(self, f"do_{arg.replace('-', '_')}", None)
            if func and func.__doc__:
                print(textwrap.dedent(func.__doc__).strip())
            else:
                print(f"No help for '{arg}'.")
        else:
            print("Available commands:")
            for name, desc in self._HELP.items():
                print(f"  {name:<15} {desc}")
            print()

    # ----------------------------------------------------------- core actions
    def do_fetch(self, _):
        """Fetch and cache *all* RFC metadata from the IETF site."""
        client.fetch_metadata(save=True)

    def do_build_faiss(self, _):
        """Build / update FAISS index from the latest saved vectors."""
        build_faiss_index()

    def do_fulltext(self, arg):
        """Full‑text search (SQLite FTS5):  fulltext <keyword>."""
        if not arg:
            print("Usage: fulltext <keyword>")
            return
        for num, snippet in search_fulltext(arg):
            print(f"RFC{num}\t…{snippet.strip()}…")

    def do_index_fulltext(self, _):
        """Rebuild the FTS5 index from raw text corpus."""
        rebuild_fulltext_index()

    def do_search(self, arg):
        """Keyword search in cached metadata:  search <keyword>."""
        if not arg:
            print("Usage: search <keyword>")
            return
        for rfc in search_metadata(arg):
            print(rfc)

    def do_semsearch(self, arg):
        """Semantic search via FAISS:  semsearch <keyword>."""
        if not arg:
            print("Usage: semsearch <keyword>")
            return
        for score, num in semsearch(arg):  # <score, rfc_num>
            print(f"RFC{num}: {score:.4f}")

    def do_pin(self, arg):
        """Pin an RFC number:  pin <number>."""
        pin_rfc(arg)

    def do_unpin(self, arg):
        """Unpin an RFC number:  unpin <number>."""
        unpin_rfc(arg)

    def do_pins(self, _):
        """List pinned RFC numbers."""
        pins = list_pins()
        print(", ".join(pins) if pins else "(none pinned)")

    def do_show(self, arg):
        """Show / export RFC details:  show <number> [json|csv|md]."""
        parts = arg.split()
        if not parts:
            print("Usage: show <number> [json|csv|md]")
            return
        num = parts[0]
        fmt = parts[1].lower() if len(parts) > 1 else "json"
        save_dir = Path("data") / "texts"
        records = show_rfc_details(num, save_dir)
        if fmt == "json":
            print(format_json(records))
        elif fmt == "csv":
            print(format_csv(records))
        elif fmt in {"md", "markdown"}:
            print(format_md(records))
        else:
            print(f"Unknown format: {fmt}")

    def do_exit(self, _):
        """Exit the shell."""
        return True


# ---------------------------------------------------------------------------
# Click CLI definitions
# ---------------------------------------------------------------------------
@click.group()
@click.version_option(__version__)
def cli():
    """RFC Chronicle – command‑line companion for browsing RFCs."""


@cli.command("shell")
def _shell_cmd():
    """Start the interactive shell."""
    RFCChronicleShell().cmdloop()


@cli.command("build_faiss")
@click.option(
    "--vectors",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to the .npy vectors file to index",
)
@click.option(
    "--index",
    type=click.Path(writable=True, dir_okay=False, path_type=Path),
    required=True,
    help="Output FAISS index file path",
)
@click.option(
    "--index-type",
    default="flat",
    show_default=True,
    help="Index type: flat, ivf=<nlist>, hnsw",
)
def _build_faiss_cmd(vectors: Path, index: Path, index_type: str):
    """Build a FAISS index from saved sentence‑transformer vectors."""
    vecs = np.load(vectors)
    d = vecs.shape[1]

    if index_type == "flat":
        idx = faiss.IndexFlatIP(d)
    elif index_type.startswith("ivf"):
        nlist = int(index_type.split("=")[1]) if "=" in index_type else 100
        quantizer = faiss.IndexFlatIP(d)
        idx = faiss.IndexIVFFlat(quantizer, d, nlist, faiss.METRIC_INNER_PRODUCT)
        idx.train(vecs)
    elif index_type == "hnsw":
        idx = faiss.IndexHNSWFlat(d, 32)
    else:
        raise click.BadParameter(f"Unknown index type: {index_type}")

    idx.add(vecs.astype("float32"))
    faiss.write_index(idx, str(index))
    click.echo(f"✅ FAISS index '{index}' built (type: {index_type}, d={d}).")


if __name__ == "__main__":
    cli()
