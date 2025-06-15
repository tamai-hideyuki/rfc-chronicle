from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import date

import faiss
from sentence_transformers import SentenceTransformer

from .models import RfcMetadata

"""FAISS ベクトル検索ユーティリティ"""
def semsearch(query: str, topk: int = 10) -> List[Tuple[int, float]]:
    """
    与えられたクエリ文字列で FAISS インデックスを検索し、
    (RFC番号, 距離スコア) のリストを返す
    """
    model = SentenceTransformer("all-MiniLM-L6-v2")
    index = faiss.read_index(str(Path("data/faiss_index.bin")))
    docmap = json.loads(Path("data/docmap.json").read_text(encoding="utf-8"))

    q_vec = model.encode([query])
    D, I = index.search(q_vec, topk)

    return [(int(docmap[str(idx)]), float(dist)) for dist, idx in zip(D[0], I[0])]


def filter_rfcs(
    rfcs: List[RfcMetadata],
    statuses: Optional[List[str]] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    keyword: Optional[str] = None,
) -> List[RfcMetadata]:
    normalized_statuses = {s.lower() for s in statuses} if statuses else None
    filtered: List[RfcMetadata] = []

    for rfc in rfcs:
        if normalized_statuses is not None and rfc.status.lower() not in normalized_statuses:
            continue
        if date_from and rfc.date < date_from:
            continue
        if date_to   and rfc.date > date_to:
            continue
        if keyword:
            kw = keyword.lower()
            haystack = rfc.title.lower()
            if rfc.abstract:
                haystack += ' ' + rfc.abstract.lower()
            haystack += ' ' + ' '.join(rfc.extra_metadata_values())
            if kw not in haystack:
                continue
        filtered.append(rfc)

    return filtered
