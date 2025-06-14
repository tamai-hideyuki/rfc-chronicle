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

### 現在のコマンド一覧

```bash
# 1. メタデータ一覧だけ取得（件数を表示）
poetry run rfc-chronicle fetch
# → RFC-Editor から最新のメタデータ (number, title, date, status) を取得し、
#    件数をコンソールに出力します。

# 2. 詳細を含めて metadata.json に保存
poetry run rfc-chronicle fetch --save
# → ① 全メタデータ取得
#    ② data/texts/*.txt に本文をダウンロード
#    ③ 本文ヘッダ（Author, Date, Title, ほか Key:Value）をパースしてメタデータにマージ
#    ④ ./data/metadata.json に書き出します。

# 3. 全文検索インデックス(FTS5)を再構築
poetry run rfc-chronicle index-fulltext
# → ./data/metadata.json と data/texts/*.txt を読み込み、
#    SQLite FTS5 仮想テーブルを作り直します。

# 4. キーワード全文検索
poetry run rfc-chronicle fulltext <query> [--limit N]
# → FTS5 インデックスを検索し、
#    マッチした RFC 番号・タイトル・スニペットを上位 N 件表示します。
#    N を省略するとデフォルト20件。

# 5. RFC詳細表示
poetry run rfc-chronicle show <number> [--output md|json|csv]
# → 指定RFC番号のメタデータ+本文を出力。
#    --output md   : Markdown 形式
#    --output json : JSON 形式
#    --output csv  : CSV 形式

# 6. メタデータ絞り込み検索
poetry run rfc-chronicle search [--from-date YYYY] [--to-date YYYY] [--keyword KEYWORD]
# → キャッシュ済み metadata.json を対象に、
#    発行年(from/to) やタイトルのキーワードでフィルタした一覧を JSON で返します。

# 7. RFCをピン留め
poetry run rfc-chronicle pin <number>
# → よく使うRFC番号をローカルに “ピン” して登録します。

# 8. ピンを解除
poetry run rfc-chronicle unpin <number>
# → 登録済みのピンを削除します。

# 9. ピン一覧表示
poetry run rfc-chronicle pins
# → 現在ピン留め中のRFC番号を一覧表示します。

# 10. セマンティック検索（未実装）
# poetry run rfc-chronicle semsearch <query>
# → 将来的にベクトル検索（sentence-transformers + FAISS）による
#    意味的に近いRFCの検索を行います。
```

