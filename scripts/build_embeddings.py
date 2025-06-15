#!/usr/bin/env python3

import os
import json
import glob
import argparse
import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
import torch

# === リソース制限設定 ===
# プロセスの優先度を下げる（他作業もできるように）
try:
    os.nice(10)
except AttributeError:
    pass

# BLAS／PyTorch の内部スレッドを絞る
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
torch.set_num_threads(1)
torch.set_num_interop_threads(1)

# === デフォルト設定 ===
DEFAULT_MODEL    = 'all-MiniLM-L6-v2'
DEFAULT_BATCH    = 32    # 小さめにしてメモリ使用量を抑制
DEFAULT_TEXT_DIR = 'data/texts'
DEFAULT_VECTORS  = 'data/vectors.npy'
DEFAULT_DOCMAP   = 'data/docmap.json'

def get_device():
    if torch.cuda.is_available():
        return 'cuda'
    if torch.backends.mps.is_available():
        return 'mps'
    return 'cpu'

def load_documents(text_dir: str) -> dict[int, str]:
    """
    text_dir/*.txt のうち、ファイル名が数字.txt のものを
    { RFC番号(int): 本文(str) } の辞書で返す
    """
    docs: dict[int, str] = {}
    for path in glob.glob(os.path.join(text_dir, '*.txt')):
        fname = os.path.basename(path)
        # '123.txt' のみを対象
        if not fname.lower().endswith('.txt'):
            continue
        base = fname[:-4]
        if not base.isdigit():
            continue
        num = int(base)
        with open(path, encoding='utf-8') as f:
            docs[num] = f.read()
    return dict(sorted(docs.items()))

def main():
    p = argparse.ArgumentParser(
        description='Build document embeddings (low-resource mode)')

    p.add_argument(
        '--model',    default=DEFAULT_MODEL,
        help='Sentence-Transformer model name')

    p.add_argument(
        '--batch',    type=int, default=DEFAULT_BATCH,
        help='Batch size for encoding')

    p.add_argument(
        '--textdir',  default=DEFAULT_TEXT_DIR,
        help='Directory of *.txt files')

    p.add_argument(
        '--out-vect', default=DEFAULT_VECTORS,
        help='Output .npy path')

    p.add_argument(
        '--out-map',  default=DEFAULT_DOCMAP,
        help='Output docmap.json path')

    args = p.parse_args()

    device = get_device()
    print(f'[INFO] Running at low priority (nice +10), device={device}, threads=1')

    os.makedirs(os.path.dirname(args.out_vect), exist_ok=True)

    # 1. ドキュメント読み込み
    docs = load_documents(args.textdir)
    if not docs:
        raise SystemExit(f'[ERROR] No RFC texts found in {args.textdir}')

    # 2. モデルロード
    print(f'[INFO] Loading model: {args.model}')
    model = SentenceTransformer(args.model, device=device)
    # DataLoader のワーカープロセス数を 0（メインプロセスのみ）にしてメモリを節約
    model._cpu_count = 0

    dim    = model.get_sentence_embedding_dimension()
    n_docs = len(docs)

    # 3. メモリマップで出力領域を確保（バッチ分のメモリしか使わないように設定）
    print(f'[INFO] Creating memmap: {args.out_vect}  shape=({n_docs},{dim})')
    vects = np.lib.format.open_memmap(
        args.out_vect,
        mode='w+',
        dtype='float32',
        shape=(n_docs, dim)
    )

    # 4. バッチエンコード → 逐次書き込み
    texts = list(docs.values())
    idxs  = list(docs.keys())
    for start in tqdm(range(0, n_docs, args.batch), desc='Encoding'):
        end   = min(start + args.batch, n_docs)
        batch = texts[start:end]
        emb   = model.encode(
            batch,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        vects[start:end, :] = emb

    # 5. docmap 保存
    print(f'[INFO] Saving docmap: {args.out_map}')
    docmap = {str(num): i for i, num in enumerate(idxs)}
    with open(args.out_map, 'w', encoding='utf-8') as f:
        json.dump(docmap, f, ensure_ascii=False, indent=2)

    print('[DONE] Embeddings built in low-resource mode.')

if __name__ == '__main__':
    main()
