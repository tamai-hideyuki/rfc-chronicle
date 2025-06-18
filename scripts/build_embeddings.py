#!/usr/bin/env python3
"""
Build RFC embeddings with all-mpnet-base-v2 in low-memory mode.
"""

import os, json, glob, argparse, numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
import torch

# === リソース制限 ===
try: os.nice(10)
except AttributeError: pass
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
torch.set_num_threads(1); torch.set_num_interop_threads(1)

# === デフォルト設定 ===
DEFAULT_MODEL    = "all-mpnet-base-v2"
DEFAULT_BATCH    = 8
DEFAULT_TEXT_DIR = "data/texts"
DEFAULT_VECTORS  = "data/vectors.npy"
DEFAULT_DOCMAP   = "data/docmap.json"

def get_device():
    if torch.cuda.is_available(): return "cuda"
    if torch.backends.mps.is_available(): return "mps"
    return "cpu"

def load_documents(text_dir: str) -> dict[int, str]:
    docs = {}
    for path in glob.glob(os.path.join(text_dir, "*.txt")):
        base = os.path.basename(path)[:-4]
        if base.isdigit():
            with open(path, encoding="utf-8") as f:
                docs[int(base)] = f.read()
    return dict(sorted(docs.items()))

def main():
    ap = argparse.ArgumentParser(description="Build MPNet embeddings.")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--batch", type=int, default=DEFAULT_BATCH)
    ap.add_argument("--textdir", default=DEFAULT_TEXT_DIR)
    ap.add_argument("--out-vect", default=DEFAULT_VECTORS)
    ap.add_argument("--out-map",  default=DEFAULT_DOCMAP)
    args = ap.parse_args()

    device = get_device()
    print(f"[INFO] device={device}, batch={args.batch}")

    docs = load_documents(args.textdir)
    if not docs: raise SystemExit(f"No texts in {args.textdir}")

    print(f"[INFO] Loading model: {args.model}")
    model = SentenceTransformer(args.model, device=device)
    model._cpu_count = 0  # DataLoader workers = 0

    dim, n = model.get_sentence_embedding_dimension(), len(docs)
    print(f"[INFO] Memmap vectors: shape=({n},{dim}) → {args.out_vect}")
    vecs = np.lib.format.open_memmap(
        args.out_vect, mode="w+", dtype="float32", shape=(n, dim)
    )

    rfc_nums, texts = list(docs.keys()), list(docs.values())
    for s in tqdm(range(0, n, args.batch), desc="Encoding"):
        e   = min(s + args.batch, n)
        emb = model.encode(texts[s:e],
                           convert_to_numpy=True,
                           normalize_embeddings=True,  # ← 追加
                           show_progress_bar=False)
        vecs[s:e, :] = emb

    print(f"[INFO] Saving docmap → {args.out_map}")
    with open(args.out_map, "w", encoding="utf-8") as f:
        json.dump({str(num): i for i, num in enumerate(rfc_nums)},
                  f, ensure_ascii=False, indent=2)
    print("[DONE] Embeddings built with MPNet.")

if __name__ == "__main__":
    main()
