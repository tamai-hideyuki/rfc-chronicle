import json
import re
from pathlib import Path
from typing import List, Tuple, Dict

import faiss
from sentence_transformers import SentenceTransformer

# データディレクトリとファイルパスの定義
_BASE_DIR = Path.cwd() / "data"
_META_PATH = _BASE_DIR / "metadata.json"
_INDEX_PATH = _BASE_DIR / "faiss_index.bin"
_DOCMAP_PATH = _BASE_DIR / "docmap.json"

# モデルとインデックスをモジュールロード時に一度だけ初期化
_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
_INDEX = faiss.read_index(str(_INDEX_PATH)) if _INDEX_PATH.exists() else None
# docmap.json を読み込んで辞書化
_DOCMAP: Dict[str, str] = json.loads(_DOCMAP_PATH.read_text(encoding="utf-8")) if _DOCMAP_PATH.exists() else {}

def semsearch(query: str, topk: int = 10) -> List[Tuple[float, str]]:
    """
    FAISS インデックスを使ったセマンティック検索。
    クエリと意味的に似ている RFC 上位 topk 件の (スコア, RFC番号) を返す。
    """
    if _INDEX is None or not _DOCMAP:
        raise RuntimeError("FAISS index or docmap not found. Please build index first.")

    # クエリをベクトル化して検索
    q_vec = _MODEL.encode([query])
    distances, indices = _INDEX.search(q_vec, topk)

    results: List[Tuple[float, str]] = []
    for dist, idx in zip(distances[0], indices[0]):
        num = _DOCMAP.get(str(idx), "")
        results.append((float(dist), num))
    return results


def search_metadata(keyword: str) -> List[str]:
    """
    metadata.json をロードし、タイトル・アブストラクト・全エントリを検索。
    マッチした RFC 番号のリスト（文字列）を返す。
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
        if m:
            results.append(m.group(1))

    return results
