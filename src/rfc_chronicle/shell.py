import cmd
import click
from .fetch_rfc import fetch_metadata
from .faiss_utils import build_faiss_index
from .fulltext import fulltext_search, rebuild_fulltext_index
from .search import search_metadata, semantic_search
from .pin import pin_rfc, unpin_rfc, list_pins
from .show import show_details

