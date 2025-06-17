#!/usr/bin/env python3
"""
NumPy ベクトルから FAISS インデックスを生成・保存するスクリプト。

機能:
  - data/vectors.npy からベクトルを読み込む
  - flat/ivf/hnsw の各種インデックスを構築
  - data/faiss_index.bin にシリアライズ保存（既存ファイルは上書き）
  - --update オプションで差分追加（既存インデックスを読み込み後、ベクトルを追加）
"""

import argparse
from pathlib import Path
import numpy as np
import faiss


def build_flat_index(vectors: np.ndarray) -> faiss.Index:
    """
    Flat (IndexFlatL2) インデックスを生成し、ベクトルを追加して返す。
    """
    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)
    return index


def build_ivf_index(vectors: np.ndarray, nlist: int = 100) -> faiss.Index:
    """
    IVF (IndexIVFFlat) インデックスを生成し、ベクトルを訓練・追加して返す。
    nlist はデータポイント数以下に自動調整される。
    """
    num_vectors, dim = vectors.shape
    # クラスタ数はデータ数以下に調整
    nlist = min(nlist, num_vectors)
    quantizer = faiss.IndexFlatL2(dim)
    index = faiss.IndexIVFFlat(quantizer, dim, nlist, faiss.METRIC_L2)
    # インデックスを訓練してから追加
    index.train(vectors)
    index.add(vectors)
    return index


def build_hnsw_index(vectors: np.ndarray, m: int = 32) -> faiss.Index:
    """
    HNSW (IndexHNSWFlat) インデックスを生成し、ベクトルを追加して返す。
    """
    dim = vectors.shape[1]
    index = faiss.IndexHNSWFlat(dim, m)
    # 構築効率パラメータ
    index.hnsw.efConstruction = 40
    index.add(vectors)
    return index


def load_vectors(path: Path) -> np.ndarray:
    """
    指定パスの .npy ファイルからベクトルを読み込み、配列を返す。
    ファイルが存在しない場合は例外を投げる。
    """
    if not path.exists():
        raise FileNotFoundError(f"ベクトルファイルが見つかりません: {path}")
    return np.load(str(path))


def save_index(index: faiss.Index, path: Path) -> None:
    """
    FAISS インデックスを指定パスにシリアライズ保存する。
    パスがなければディレクトリを作成し、既存ファイルは上書き。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(path))
    print(f"インデックスを保存しました: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="NumPy ベクトルから FAISS インデックスを生成・更新する"
    )
    parser.add_argument(
        "--vectors", "-v",
        default="data/vectors.npy",
        help="読み込むベクトルの .npy ファイルパス"
    )
    parser.add_argument(
        "--index", "-i",
        default="data/faiss_index.bin",
        help="保存/読み込みする FAISS インデックスファイルのパス"
    )
    parser.add_argument(
        "--update", "-u",
        action="store_true",
        help="既存インデックスを読み込み、新規ベクトルを追加する"
    )
    parser.add_argument(
        "--type", "-t",
        choices=["flat", "ivf", "hnsw"],
        default="flat",
        help="生成するインデックスタイプ (flat, ivf, hnsw)"
    )
    args = parser.parse_args()

    vectors_path = Path(args.vectors)
    index_path = Path(args.index)
    vectors = load_vectors(vectors_path)

    if args.update:
        # 差分追加モード: 既存インデックスを読み込み、ベクトルを追加して保存
        if not index_path.exists():
            print(f"既存インデックスが見つかりません ({index_path})。新規作成します。")
            index = build_flat_index(vectors)
        else:
            index = faiss.read_index(str(index_path))
            index.add(vectors)
        save_index(index, index_path)
    else:
        # 全量ビルドモード: type に応じたインデックスを構築
        if args.type == "flat":
            index = build_flat_index(vectors)
        elif args.type == "ivf":
            index = build_ivf_index(vectors)
        elif args.type == "hnsw":
            index = build_hnsw_index(vectors)
        save_index(index, index_path)

def build_faiss_index(
    vectors_path: str = "data/vectors.npy",
    index_path: str = "data/faiss_index.bin",
    index_type: str = "flat",
    update: bool = False,
):
    """
    Interactive Shell や CLI から呼び出しやすいラッパー関数。
    --vectors, --index, --type, --update オプションと同等の挙動をします。
    """
    import sys
    # argparse で使っている main() を直接呼び出すために sys.argv を一時置き換え
    old_argv = sys.argv[:]
    sys.argv = ["build_faiss", "--vectors", vectors_path, "--index", index_path]
    if update:
        sys.argv.append("--update")
    if index_type != "flat":
        sys.argv.extend(["--type", index_type])
    try:
        # スクリプト中で定義された main() を呼び出す
        main()
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    main()
