# rfc-chronicle

![PyPI version](https://img.shields.io/pypi/v/rfc-chronicle.svg)
![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)
![Poetry](https://img.shields.io/badge/poetry-1.5%2B-blue.svg)
![Click](https://img.shields.io/badge/click-8.1%2B-blue.svg)
![FAISS](https://img.shields.io/badge/faiss-enabled-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)

## 概要

`rfc-chronicle` は [RFC-Editor](https://www.rfc-editor.org/) から
RFC（Request for Comments）のメタデータや本文をローカルに取り込み、
キーワード全文検索・将来のベクトル検索・各種エクスポートを
CLI から手軽に行えるツールです。

---

## インストール

```bash
git clone https://github.com/tamai-hideyuki/rfc-chronicle.git

cd rfc-chronicle

poetry install
```

---

## 機能一覧

1. **メタデータ取得**

- RFC 番号・タイトル・日付・ステータスを一覧取得
- 本文ヘッダ（Author, Date, Title など）を細かくパースしてマージ

2. **本文ダウンロード**

- 複数RFCを一括／範囲指定で取得
- 存在しない番号（404）は自動スキップ

3. **全文検索（FTS5）**

- SQLite FTS5 で高速キーワード検索
- スニペット付きでヒット箇所を表示

4. **意味的検索（ベクトル検索・予定）**

- Sentence‐Transformers + FAISS によるセマンティック検索
- 類似RFCレコメンド

5. **全文検索DB再構築**

- 差分更新 or 完全再構築
- Porterステミング対応

6. **詳細表示**

- JSON / CSV / Markdown 形式でRFC詳細を出力

7. **ピン機能**

- よく使うRFCをピン留め・解除・一覧表示

---

## 使い方

### 0. 仮想環境有効化

```bash
# (1) venv を作成（プロジェクト直下に .venv フォルダが作られる）
python3 -m venv .venv

# (2) 仮想環境を有効化
source .venv/bin/activate
```

### 1. メタデータ取得

```bash
# 一覧を取得（件数のみ表示）
poetry run rfc-chronicle fetch

# ヘッダ付き詳細もマージして ./data/metadata.json に保存
poetry run rfc-chronicle fetch --save
```

### 2. 本文一括ダウンロード

```bash
# scripts/download_all.sh を使って ./data/texts/*.txt を一括取得
./scripts/download_all.sh
```

### 3. 全文検索インデックス構築

```bash
poetry run rfc-chronicle index-fulltext
```

### 4. キーワード全文検索

```bash
# 本文内の “OAuth” を含むRFCを上位10件表示
poetry run rfc-chronicle fulltext OAuth --limit 10
```

### 5. 意味的検索（将来）

```bash
# セマンティック検索（実装後）
poetry run rfc-chronicle semsearch "セキュリティ トランスポート"
```

### 6. RFC詳細表示

```bash
# Markdown形式でRFC1を表示
poetry run rfc-chronicle show 1 --output md

# JSON形式でRFC791を表示
poetry run rfc-chronicle show 791 --output json

# CSV形式でRFC26を表示
poetry run rfc-chronicle show 26 --output csv
```

### 7. メタデータ絞り込み検索

```bash
# タイトルに "Network" を含むRFCをリスト
poetry run rfc-chronicle search --keyword Network
```

### 8. ピン機能

```bash
poetry run rfc-chronicle pin 1      # ピン留め
poetry run rfc-chronicle unpin 1    # ピン解除
poetry run rfc-chronicle pins       # ピン一覧
```

---

| コマンド                                                                        | 説明                                                                      |
| --------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `rfc-chronicle fetch`                                                       | RFC メタデータ一覧を取得し、件数を表示                                                   |
| `rfc-chronicle fetch --save`                                                | メタデータ＋本文ヘッダを `data/metadata.json` に保存、本文テキストを `data/texts/` にダウンロード     |
| `rfc-chronicle index-fulltext`                                              | SQLite FTS5 で全文検索インデックスを再構築 (`data/metadata.json`＋`data/texts/` → FTS5) |
| `rfc-chronicle fulltext <query> [--limit N]`                                | キーワード全文検索。デフォルト上位20件、`--limit` で表示件数を調整                                 |
| `rfc-chronicle show <RFC番号> [--output md\|json\|csv]`                       | 指定RFCの詳細（メタデータ＋本文）を Markdown/JSON/CSV で出力                               |
| `rfc-chronicle search [--from-date YYYY] [--to-date YYYY] [--keyword WORD]` | 発行年やタイトルキーワードでメタデータを絞り込み、JSON で出力                                       |
| `rfc-chronicle pin <RFC番号>`                                                 | 指定RFCを「ピン留め」（お気に入り登録）                                                   |
| `rfc-chronicle unpin <RFC番号>`                                               | 指定RFCのピンを解除                                                             |
| `rfc-chronicle pins`                                                        | 現在ピン留め中のRFC番号一覧を表示                                                      |

## 補助スクリプト

- 埋め込み生成
```bash
# 説明：全文テキストを Sentence-Transformers（all-MiniLM-L6-v2）で埋め込み → vectors.npy／docmap.json に出力

python scripts/build_embeddings.py \
  --textdir data/texts \
  --out-vect data/vectors.npy \
  --out-map  data/docmap.json \
  --batch   32
```

- 分析＆可視化
```bash
# 1) 意味的検索 (Semantic Search)
python scripts/analyze_embeddings.py search <RFC番号> [--topk N]

# 2) 類似度計算 (Similarity)
python scripts/analyze_embeddings.py sim <RFC番号1> <RFC番号2>

# 3) クラスタリング＆可視化 (Clustering & Visualization)
python scripts/analyze_embeddings.py cluster \
  --k <クラスタ数> \
  [--sample <サンプル件数>] \
  [--perplexity <t-SNE perplexity>] 
```

---

## 各コマンドの使い方例

```bash

# メタデータ＋本文を取得
rfc-chronicle fetch --save

# “OAuth” を含む全文検索（上位10件）
rfc-chronicle fulltext OAuth --limit 10

# RFC1 を Markdown で表示
rfc-chronicle show 1 --output md

# 発行年 1990〜2000 の RFC を一覧
rfc-chronicle search --from-date 1990 --to-date 2000

# RFC123 に意味的に近い上位5件
python scripts/analyze_embeddings.py search 123 --topk 5

# RFC123 と RFC456 の類似度を計算
python scripts/analyze_embeddings.py sim 123 456

# 全文書を8クラスタに分け、サンプル2000件で可視化
python scripts/analyze_embeddings.py cluster --k 8 --sample 2000 --perplexity 40

```
