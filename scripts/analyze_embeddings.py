#!/usr/bin/env python3

import json
import argparse
import numpy as np

# --- デフォルト設定 ---
VECTORS_PATH = 'data/vectors.npy'
DOCMAP_PATH  = 'data/docmap.json'
EPS = 1e-8  # ゼロ割防止用

def load_data(vect_path: str, map_path: str):
    vecs   = np.load(vect_path, mmap_mode='r')
    docmap = json.load(open(map_path, 'r'))
    # 逆引きマップ：行インデックス → RFC番号(int)
    revmap = {int(idx): int(rfc) for rfc, idx in docmap.items()}
    return vecs, docmap, revmap

def semantic_search(vecs, docmap, revmap, query_num, topk):
    """
    手動コサイン類似度計算 + np.argpartition で高速上位抽出
    """
    idx = docmap.get(str(query_num))
    if idx is None:
        raise ValueError(f'RFC{query_num} が見つかりません')

    # クエリベクトルと全体ベクトルを L2 正規化
    q = vecs[idx].astype(np.float64)
    V = vecs.astype(np.float64)
    q_norm = np.linalg.norm(q) + EPS
    V_norm = np.linalg.norm(V, axis=1) + EPS
    sims = (V @ q) / (V_norm * q_norm)  # shape (N,)

    # NaN を -1.0 に置換（ゼロベクトル対策）
    sims = np.nan_to_num(sims, nan=-1.0)

    # 自身を除いた上位 topk を argpartition で取得
    # topk+1 件を取って自身を削除し、最終 topk 件に絞る
    cand = np.argpartition(-sims, topk + 1)[: topk + 1].tolist()
    cand = [i for i in cand if i != idx]
    cand = sorted(cand, key=lambda i: -sims[i])[:topk]

    return [(revmap[i], float(sims[i])) for i in cand]

def calc_similarity(vecs, docmap, revmap, r1, r2):
    """
    手動コサイン類似度 + ユークリッド距離
    """
    i1 = docmap.get(str(r1))
    i2 = docmap.get(str(r2))
    if i1 is None or i2 is None:
        raise ValueError('指定のRFCが見つかりません')

    v1 = vecs[i1].astype(np.float64)
    v2 = vecs[i2].astype(np.float64)
    norm1 = np.linalg.norm(v1) + EPS
    norm2 = np.linalg.norm(v2) + EPS

    cos_sim = float((v1 @ v2) / (norm1 * norm2))
    euclid  = float(np.linalg.norm(v1 - v2))
    return cos_sim, euclid

def cluster_and_plot(vecs, revmap, n_clusters, sample_n, perplexity):
    from sklearn.cluster import KMeans
    from sklearn.manifold import TSNE
    from matplotlib import pyplot as plt

    n_docs = vecs.shape[0]

    # サンプリング（必要に応じて全件 or 指定件数）
    if 0 < sample_n < n_docs:
        rng = np.random.default_rng(0)
        idxs = rng.choice(n_docs, sample_n, replace=False)
        data = vecs[idxs]
        rev = {j: revmap[i] for j, i in enumerate(idxs)}
    else:
        data = vecs
        rev = revmap

    # クラスタリング
    kmeans = KMeans(n_clusters=n_clusters, random_state=0, n_init=10)
    labels = kmeans.fit_predict(data)

    # 次元削減 (t-SNE)
    tsne = TSNE(
        n_components=2,
        init='pca',
        perplexity=perplexity,
        learning_rate='auto',
        random_state=0,
        verbose=1
    ).fit_transform(data)

    # プロット
    plt.figure(figsize=(8, 6))
    plt.scatter(tsne[:,0], tsne[:,1], c=labels, s=10, cmap='tab10')
    plt.title(f'RFC Embedding Clusters (k={n_clusters})')
    plt.xlabel('t-SNE dim 1')
    plt.ylabel('t-SNE dim 2')
    plt.tight_layout()
    plt.show()

def main():
    p = argparse.ArgumentParser(description='Analyze RFC embeddings')
    p.add_argument('--vect', default=VECTORS_PATH,
                   help='埋め込みベクトルファイルパス')
    p.add_argument('--map',  default=DOCMAP_PATH,
                   help='RFC→行マップJSONパス')
    sub = p.add_subparsers(dest='cmd', required=True)

    # semantic search
    s = sub.add_parser('search', help='意味的に近いRFCを検索')
    s.add_argument('rfc',   type=int, help='クエリにするRFC番号')
    s.add_argument('--topk', type=int, default=5,
                   help='返す件数')

    # similarity
    t = sub.add_parser('sim', help='2つのRFC間の類似度計算')
    t.add_argument('r1', type=int, help='RFC番号①')
    t.add_argument('r2', type=int, help='RFC番号②')

    # clustering & visualization
    c = sub.add_parser('cluster', help='クラスタリング＆可視化')
    c.add_argument('--k',          type=int, default=8,
                   help='クラスタ数')
    c.add_argument('--sample',     type=int, default=0,
                   help='t-SNE用サンプル件数 (0=全件)')
    c.add_argument('--perplexity', type=float, default=30,
                   help='t-SNE perplexity')

    args = p.parse_args()
    vecs, docmap, revmap = load_data(args.vect, args.map)

    if args.cmd == 'search':
        res = semantic_search(vecs, docmap, revmap, args.rfc, args.topk)
        print(f'RFC{args.rfc} に意味的に近い上位 {args.topk} 件:')
        for num, score in res:
            print(f'  RFC{num}: {score:.4f}')

    elif args.cmd == 'sim':
        cos_s, euc = calc_similarity(vecs, docmap, revmap, args.r1, args.r2)
        print(f'RFC{args.r1} ↔ RFC{args.r2}:')
        print(f'  Cosine similarity : {cos_s:.4f}')
        print(f'  Euclidean distance : {euc:.4f}')

    elif args.cmd == 'cluster':
        print(f'Clustering into k={args.k}, sample={args.sample or "all"} docs, '
              f'perplexity={args.perplexity}...')
        cluster_and_plot(vecs, revmap, args.k, args.sample, args.perplexity)

if __name__ == '__main__':
    main()
