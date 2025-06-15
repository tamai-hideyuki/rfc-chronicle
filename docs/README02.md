# rfc-chronicle

![PyPI version](https://img.shields.io/pypi/v/rfc-chronicle.svg) ![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg) ![Poetry](https://img.shields.io/badge/poetry-1.5%2B-blue.svg) ![Click](https://img.shields.io/badge/click-8.1%2B-blue.svg) ![FAISS](https://img.shields.io/badge/faiss-enabled-brightgreen.svg) ![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)

`rfc-chronicle` は、RFC ドキュメントのメタデータ取得、全文検索、FAISS ベクトル検索を一気通貫で行える CLI ツールです。

## インストール

```bash
git clone https://github.com/tamai-hideyuki/rfc-chronicle.git
cd rfc-chronicle
poetry install
poetry shell
```

## 基本コマンド

* **fetch**: 全 RFC のメタデータを取得（`--save` で本文ヘッダ情報付きで保存）

  ```bash
  rfc-chronicle fetch            # メタデータ一覧のみ取得
  rfc-chronicle fetch --save     # 本文ヘッダも含めて data/metadata.json に保存
  ```

* **search**: 保存済みメタデータを絞り込み検索

  ```bash
  rfc-chronicle search --from-date 2000 --to-date 2010 --keyword OAuth
  ```

* **show**: 指定 RFC の詳細（メタデータ＋本文）を表示

  ```bash
  rfc-chronicle show 7231           # Markdown 形式で表示
  rfc-chronicle show 7231 --output json
  ```

* **fulltext**: FTS5 による全文検索

  ```bash
  # まず DB の構築
  rfc-chronicle index-fulltext

  # クエリ実行
  rfc-chronicle fulltext "authentication token" -n 10
  ```

* **build-faiss**: FAISS ベクトル検索用インデックスを生成・更新

  ```bash
  # flat インデックスを生成
  rfc-chronicle build-faiss \
    --vectors data/vectors.npy \
    --index   data/faiss_flat.bin

  # IVF インデックスを生成 (デフォルトインデックスファイル: data/faiss_index.bin)
  rfc-chronicle build-faiss -t ivf

  # HNSW インデックスを生成
  rfc-chronicle build-faiss -t hnsw

  # 既存インデックスに差分ベクトルを追加
  # (事前に data/new_vectors.npy を用意)
  rfc-chronicle build-faiss -u \
    --vectors data/new_vectors.npy
  ```

## 開発

1. リポジトリをクローン
2. Poetry で依存をインストール
3. `scripts/build_vectors.py` などを実行して `data/vectors.npy` を用意
4. 上記コマンドを試す

## ライセンス

MIT
