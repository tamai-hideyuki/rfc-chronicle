#!/usr/bin/env python3

import json
import argparse
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt

# --- 設定 ---
VECTORS_PATH = 'data/vectors.npy'
DOCMAP_PATH  = 'data/docmap.json'

def load_data():
    vecs   = np.load(VECTORS_PATH, mmap_mode='r')
    docmap = json.load(open(DOCMAP_PATH, 'r'))
    # 逆引きマップ：行インデックス → RFC番号
    revmap = {int(v): int(k) for k, v in docmap.items()}
    return vecs, docmap, revmap

def semantic_search(vecs, docmap, revmap, query_num, topk):
    idx     = docmap[str(query_num)]
    q_vec   = vecs[idx:idx+1]
    sims    = cosine_similarity(q_vec, vecs)[0]
    best_i  = sims.argsort()[::-1][1:topk+1]
    return [(revmap[i], float(sims[i])) for i in best_i]

def calc_similarity(vecs, docmap, r1, r2):
    v1      = vecs[docmap[str(r1)]]
    v2      = vecs[docmap[str(r2)]]
    cos_sim = float(cosine_similarity(v1[np.newaxis], v2[np.newaxis])[0][0])
    euclid  = float(np.linalg.norm(v1 - v2))
    return cos_sim, euclid

def cluster_and_plot(vecs, n_clusters):
    kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(vecs)
    labels = kmeans.labels_
    tsne   = TSNE(n_components=2, random_state=0).fit_transform(vecs)

    plt.figure(figsize=(8, 6))
    plt.scatter(tsne[:,0], tsne[:,1], c=labels, s=10, cmap='tab10')
    plt.title(f'RFC Embedding Clusters (k={n_clusters})')
    plt.xlabel('t-SNE dim 1')
    plt.ylabel('t-SNE dim 2')
    plt.tight_layout()
    plt.show()

def main():
    p = argparse.ArgumentParser(description='Analyze RFC embeddings')
    sub = p.add_subparsers(dest='cmd', required=True)

    # semantic search
    s = sub.add_parser('search', help='Semantic search for a given RFC number')
    s.add_argument('rfc',   type=int, help='RFC number to query')
    s.add_argument('--topk', type=int, default=5, help='Number of results to return')

    # similarity
    t = sub.add_parser('sim', help='Calculate similarity between two RFCs')
    t.add_argument('r1', type=int, help='First RFC number')
    t.add_argument('r2', type=int, help='Second RFC number')

    # clustering & visualization
    c = sub.add_parser('cluster', help='Cluster & visualize all RFCs')
    c.add_argument('--k', type=int, default=8, help='Number of clusters')

    args = p.parse_args()

    vecs, docmap, revmap = load_data()

    if args.cmd == 'search':
        results = semantic_search(vecs, docmap, revmap, args.rfc, args.topk)
        print(f'Semantic search for RFC {args.rfc}:')
        for num, score in results:
            print(f'  RFC{num}: similarity={score:.4f}')

    elif args.cmd == 'sim':
        cos_sim, euclid = calc_similarity(vecs, docmap, args.r1, args.r2)
        print(f'RFC{args.r1} ↔ RFC{args.r2}:')
        print(f'  Cosine similarity = {cos_sim:.4f}')
        print(f'  Euclidean distance = {euclid:.4f}')

    elif args.cmd == 'cluster':
        print(f'Clustering into k={args.k} groups and visualizing with t-SNE...')
        cluster_and_plot(vecs, args.k)

if __name__ == '__main__':
    main()
