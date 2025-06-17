## インタラクティブシェル

**実行方法**

```bash

poetry run rfc-chronicle shell
```

```bash

poetry run rfc-chronicle shell

Welcome to RFC Chronicle Shell. Type help or ? to list commands.

> help
Commands:
  fetch           全 RFC メタデータを取得・保存
  build-faiss     NumPy ベクトルから FAISS インデックスを生成/更新
  fulltext        SQLite FTS5 で全文検索
  index-fulltext  FTS5 全文検索 DB を再構築
  search          キャッシュ済みメタデータをキーワードで絞り込み
  semsearch       FAISS を用いたセマンティック検索
  pin             RFC をピン留め
  pins            ピン一覧を表示
  show            RFC 詳細を表示・エクスポート
  unpin           ピンを解除
  exit            シェルを終了

>
```

**入力例**

```bash
poetry install
poetry run rfc-chronicle shell
> help
> fulltext OAuth
> search JWT
> semsearch OAuth
> show 6749 md
```