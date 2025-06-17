# src/rfc_chronicle/search.py
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import date

import faiss
from sentence_transformers import SentenceTransformer

from .models import RfcMetadata

# --- File paths for resources (relative to project root) ---
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _PROJECT_ROOT / "data"
_INDEX_PATH = _DATA_DIR / "faiss_index.bin"
_DOCMAP_PATH = _DATA_DIR / "docmap.json"
_META_PATH = _DATA_DIR / "metadata.json"


def semsearch(query: str, topk: int = 10) -> List[Tuple[int, float]]:
    """
    Perform a semantic search using FAISS.
    Loads the FAISS index, document map, and embedding model on demand.
    Returns a list of tuples (RFC number, distance score).
    Raises RuntimeError if resources are missing.
    """
    if not _INDEX_PATH.exists():
        raise RuntimeError(f"FAISS index not found at {_INDEX_PATH}")
    if not _DOCMAP_PATH.exists():
        raise RuntimeError(f"Document map not found at {_DOCMAP_PATH}")

    model = SentenceTransformer("all-MiniLM-L6-v2")
    index = faiss.read_index(str(_INDEX_PATH))
    with open(_DOCMAP_PATH, encoding="utf-8") as f:
        docmap: dict[str, int] = json.load(f)

    q_vec = model.encode([query])
    distances, indices = index.search(q_vec, topk)

    results: List[Tuple[int, float]] = []
    for dist, idx in zip(distances[0], indices[0]):
        rfc_no = docmap.get(str(idx))
        if rfc_no is None:
            continue
        results.append((rfc_no, float(dist)))
    return results


def filter_rfcs(
    rfcs: List[RfcMetadata],
    statuses: Optional[List[str]] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    keyword: Optional[str] = None,
) -> List[RfcMetadata]:
    """
    Filter a list of RfcMetadata objects by:
      - Publication status
      - Date range (inclusive)
      - Keyword (in title, abstract, extra metadata)
    Returns the filtered list.
    """
    statuses_norm = {s.lower() for s in statuses} if statuses else None
    keyword_norm = keyword.lower() if keyword else None

    filtered: List[RfcMetadata] = []
    for r in rfcs:
        if statuses_norm and r.status.lower() not in statuses_norm:
            continue
        if date_from and r.date < date_from:
            continue
        if date_to and r.date > date_to:
            continue
        if keyword_norm:
            parts = [r.title or "", r.abstract or ""]
            parts.extend(r.extra_metadata_values())
            haystack = " ".join(parts).lower()
            if keyword_norm not in haystack:
                continue
        filtered.append(r)
    return filtered


def search_metadata(keyword: str) -> List[str]:
    """
    Load metadata.json and return RFC numbers where keyword appears
    in title, abstract, or extra metadata.
    Raises RuntimeError if metadata file is missing.
    """
    if not _META_PATH.exists():
        raise RuntimeError(f"Metadata file not found at {_META_PATH}")
    raw = json.loads(_META_PATH.read_text(encoding="utf-8"))
    rfcs: List[RfcMetadata] = []
    for entry in raw:
        # Parse date if present, with fallback for non-ISO formats
        dt = entry.get("date")
        if dt:
            try:
                rfc_date = date.fromisoformat(dt)
            except (ValueError, TypeError):
                # e.g., 'April 1969' or other non-ISO formats
                rfc_date = date.min
        else:
            rfc_date = date.min
        rfcs.append(RfcMetadata(
            number=int(entry.get("number", "0")),
            title=entry.get("title", ""),
            abstract=entry.get("abstract", ""),
            date=rfc_date,
            status=entry.get("status", ""),
            extra_metadata=entry
        ))
    filtered = filter_rfcs(rfcs, keyword=keyword)
    return [str(r.number) for r in filtered]
