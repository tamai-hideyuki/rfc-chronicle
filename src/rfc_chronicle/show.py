from pathlib import Path
from rfc_chronicle.fetch_rfc import client


DATA_DIR = Path(__file__).parent.parent / "data" / "texts"

def show_rfc_details(rfc_num: int) -> dict:
    """
    Download (if needed) and return the full metadata + body for RFC {rfc_num}.
    """
    # ensure the directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # fetch_details will pull from the network once and then cache locally
    return client.fetch_details(rfc_num, save_dir=DATA_DIR, use_conditional=True)
