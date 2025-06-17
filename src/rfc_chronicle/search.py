import json
import re
from pathlib import Path
from typing import List, Tuple

import faiss
from sentence_transformers import SentenceTransformer

# パス定義（必要に応じて調整）
_META_PATH = Path.cwd() / "data" / "metadata.json"
_FAISS_INDEX_PATH = Path.cwd() / "data" / "faiss_index.bin"
_DOCPATH = Path.cwd() / "data" / "docmap.json"


def search_metadata(keyword: str) -> List[str]:
    """
    metadata.json をロードし、タイトル・アブストラクト・全エントリを検索して
    マッチした RFC 番号のリスト（文字列）を返します。
    """
    if not _META_PATH.exists():
        raise RuntimeError(f"Metadata file not found at {_META_PATH}")

    data = json.loads(_META_PATH.read_text(encoding="utf-8"))
    kw = keyword.lower()
    results: List[str] = []

    for entry in data:
        title = entry.get("title", "") or ""
        abstract = entry.get("abstract", "") or ""
        extra = json.dumps(entry)
        text_blob = f"{title}\n{abstract}\n{extra}".lower()
        if kw not in text_blob:
            continue
        raw_num = entry.get("number", "")
        m = re.search(r"(\d+)", raw_num)
        if not m:
            continue
        results.append(m.group(1))

    return results


def semsearch(query: str, topk: int = 10) -> List[Tuple[float, str]]:
    """
    FAISS インデックスを使ったベクトル検索（セマンティック検索）。
    クエリと意味的に似ている RFC 上位 topk 件の
    (スコア, RFC番号) を返します。
    """
    if not _FAISS_INDEX_PATH.exists() or not _DOCPATH.exists():
        raise RuntimeError("FAISS index or docmap not found. Please build index first.")

    # モデルとインデックスロード
    model = SentenceTransformer("all-MiniLM-L6-v2")
    index = faiss.read_index(str(_FAISS_INDEX_PATH))
    docmap = json.loads(_DOCPATH.read_text(encoding="utf-8"))

    # クエリ埋め込み
    q_vec = model.encode([query])
    D, I = index.search(q_vec, topk)

    results: List[Tuple[float, str]] = []
    for dist, idx in zip(D[0], I[0]):
        rfc_num = docmap.get(str(idx), "")
        results.append((dist, rfc_num))

    return results
