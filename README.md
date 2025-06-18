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
## RFC Chronicle — 実装済み機能まとめ

| 大分類           | 機能                   | 概要                                                                                          | 代表エンドポイント / CLI                      |
| ------------- | -------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------ |
| **メタデータ**     | メタデータ取得 (`fetch`)    | IETF 公式 JSON をダウンロード／キャッシュ                                                                  | `GET /api/metadata?save=<bool>`      |
|               | メタデータ検索 (`search`)   | タイトル・アブストラクト・全要素にキーワード一致                                                                    | `GET /api/search?q=<kw>`             |
| **全文検索**      | FTS5 インデックス再構築       | `data/texts/*.txt` から `fulltext.db` を生成                                                     | CLI: `index-fulltext`                |
|               | 全文検索 (`fulltext`)    | 本文を SQLite FTS5 で全文検索し、スニペット付きで返却                                                           | `GET /api/fulltext?q=<kw>&limit=<n>` |
| **セマンティック検索** | FAISS インデックス生成       | 埋め込み（vectors.npy）→ `faiss_index.bin`                                                        | CLI: `build-faiss`                   |
|               | セマンティック検索            | Sentence-Transformers + FAISS でベクトル類似検索<br>返却 JSON: `[{ "num": "5849", "score": 0.72 }, …]` | `GET /api/semsearch?q=<kw>&topk=<n>` |
| **詳細取得**      | RFC 本文＋ヘッダ取得         | 条件付き GET 対応でキャッシュ                                                                           | `GET /api/show/{rfc_num}`            |
| **ピン留め**      | pin / unpin / pins   | お気に入り RFC 管理 (JSON `pins.json`)                                                             | CLI: `pin 1234` 等                    |
| **CLI シェル**   | `shell` コマンド         | すべてのサブコマンドを対話的に呼び出し                                                                         |                                      |
| **Web UI**    | 単一 HTML (Vanilla JS) | - 3 つの検索タブ<br>- クリックで詳細ポップアップ<br>- エラー／ローディング表示                                             |                                      |


---

### 使い方

## 1. 初期データ取得

```bash
# RFC メタデータ＆本文をローカルにダウンロード
# --no-text を付けるとメタデータのみ取得
# --force で既存データを上書き

rfc-chronicle fetch
```
## 2. インタラクティブシェル

```bash
rfc-chronicle shell
```
**起動後、プロンプト（> ）で以下のコマンドを実行できます。**

| コマンド                | 概要                         |     |                 |
| ------------------- | -------------------------- | --- | --------------- |
| `fetch [--no-text]` | メタデータ／本文の取得                |     |                 |
| `search <キーワード>`    | メタデータ（タイトル・要約など）検索         |     |                 |
| `fulltext <キーワード>`  | 本文全文検索                     |     |                 |
| `semsearch <クエリ>`   | FAISS を用いたセマンティック検索（類似度検索） |     |                 |
| `index_fulltext`    | 本文全文検索用データベースの再構築          |     |                 |
| `build_faiss …`     | ベクトルインデックスの構築／更新           |     |                 |
| `pin <RFC番号>`       | RFC を “ピン留め”               |     |                 |
| `unpin <RFC番号>`     | ピン留めを解除                    |     |                 |
| `pins`              | ピン留め一覧表示                   |     |                 |
| `show <RFC番号>`      | RFC の詳細表示（\`-f json        | csv | md\` でフォーマット指定） |
| `help`              | コマンド一覧／ヘルプ表示               |     |                 |
| `exit`              | シェルを終了                     |     |                 |


## 3. ワンライナーでの利用例

- メタデータ検索
```bash
rfc-chronicle search "OAuth"
```

- 全文検索
```bash
rfc-chronicle fulltext "key exchange"
```


- セマンティック検索
```bash
rfc-chronicle semsearch "JSON Web Token" --topk 5
```


- ベクトルインデックス構築
```bash
rfc-chronicle build-faiss \
  --vectors data/vectors.npy \
  --index  data/faiss_index.bin \
  --type   hnsw
```


- RFC をピン留め／解除
```bash
rfc-chronicle pin   7230
rfc-chronicle unpin 7230
rfc-chronicle pins
```


- Markdown 形式で詳細を出力
```bash
rfc-chronicle show 2119 -f md > rfc2119.md
```

## ブラウザ版

```bash
docker/ docker compose up -d --build
```
