import os
import json
import re
from pathlib import Path
from typing import List, Tuple, Dict

import torch
import faiss
from sentence_transformers import SentenceTransformer

# --- データディレクトリとファイルパスの定義 ---
BASE_DIR    = Path.cwd() / "data"
META_PATH   = BASE_DIR / "metadata.json"
INDEX_PATH  = BASE_DIR / "faiss_index.bin"
DOCMAP_PATH = BASE_DIR / "docmap.json"

# --- モデル設定（環境変数で上書き可能） ---
# 環境変数 RFC_EMBED_MODEL が設定されていればそちらを使い、未設定時は MPNet をデフォルトに
DEFAULT_MODEL = os.getenv("RFC_EMBED_MODEL", "all-mpnet-base-v2")

# --- デバイス判定 ---
if torch.cuda.is_available():
    DEVICE = "cuda"
elif torch.backends.mps.is_available():
    DEVICE = "mps"
else:
    DEVICE = "cpu"

# --- モデルとインデックスをモジュールロード時に一度だけ初期化 ---
_MODEL = SentenceTransformer(DEFAULT_MODEL, device=DEVICE)
_INDEX = faiss.read_index(str(INDEX_PATH)) if INDEX_PATH.exists() else None

# --- docmap を読み込んで辞書化 ---
_DOCMAP: Dict[str, str] = {}
if DOCMAP_PATH.exists():
    _DOCMAP = json.loads(DOCMAP_PATH.read_text(encoding="utf-8"))

def semsearch(query: str, topk: int = 10) -> List[Tuple[float, str]]:
    """
    FAISS インデックスを用いたセマンティック検索。
    クエリをベクトル化し、類似度上位 topk 件の (スコア, RFC番号) を返す。
    """
    if _INDEX is None or not _DOCMAP:
        raise RuntimeError("FAISS index or docmap not found. Please build index first.")

    # クエリ埋め込みを生成（バッチサイズ=1）
    q_vec = _MODEL.encode([query], convert_to_numpy=True)
    # 次元チェック
    if q_vec.shape[1] != _INDEX.d:
        raise RuntimeError(f"Query dimension {q_vec.shape[1]} != index dimension {_INDEX.d}")

    # FAISS 検索（内積距離で類似度を取得）
    distances, indices = _INDEX.search(q_vec.astype('float32'), topk)

    # 結果組み立て
    results: List[Tuple[float, str]] = []
    for dist, idx in zip(distances[0], indices[0]):
        rfc_num = _DOCMAP.get(str(idx), "")
        results.append((float(dist), rfc_num))
    return results

def search_metadata(keyword: str) -> List[str]:
    """
    metadata.json をロードし、タイトル・アブストラクト・その他フィールドから
    キーワードにマッチする RFC 番号のリストを返す。
    """
    if not META_PATH.exists():
        raise RuntimeError(f"Metadata file not found at {META_PATH}")

    entries = json.loads(META_PATH.read_text(encoding="utf-8"))
    kw = keyword.lower()
    results: List[str] = []

    for entry in entries:
        # タイトル・アブストラクト・全フィールドJSONを結合して検索
        text_blob = " ".join([
            entry.get("title", ""),
            entry.get("abstract", ""),
            json.dumps(entry, ensure_ascii=False)
        ]).lower()

        if kw not in text_blob:
            continue

        # RFC番号を抽出して追加
        num = ""
        match = re.search(r"(\d+)", entry.get("number", ""))
        if match:
            num = match.group(1)
        results.append(num)

    return results
