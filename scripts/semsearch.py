import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import sys
import click

@click.command()
@click.argument("query")
@click.option("--topk", default=10, help="返す上位件数")
def semsearch(query: str, topk: int):
    # 1) model・index・docmap のロード
    model = SentenceTransformer("all-MiniLM-L6-v2")
    index = faiss.read_index("data/faiss_index.bin")
    with open("data/docmap.json", "r", encoding="utf-8") as f:
        docmap = json.load(f)

    # 2) クエリをベクトル化して検索
    q_vec = model.encode([query])
    D, I = index.search(q_vec, topk)

    # 3) 結果を出力
    for dist, idx in zip(D[0], I[0]):
        rfc_num = docmap[str(idx)]
        print(f"RFC{rfc_num}\t{dist:.4f}")

if __name__ == "__main__":
    semsearch()  # noqa
