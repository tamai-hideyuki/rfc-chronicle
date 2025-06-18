import faiss
from sentence_transformers import SentenceTransformer
import json
from pathlib import Path

# ──── ここで一度だけロードするようにしてみる ────
_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
_INDEX = faiss.read_index(str(Path.cwd() / "data" / "faiss_index.bin"))
_DOCMAP = json.loads((Path.cwd() / "data" / "docmap.json").read_text("utf-8"))

def semsearch(query: str, topk: int = 10):
    q_vec = _MODEL.encode([query])
    D, I = _INDEX.search(q_vec, topk)
    return [(float(dist), _DOCMAP.get(str(idx), "")) for dist, idx in zip(D[0], I[0])]
