## poetry run rfc-chronicle --help

**2025/6/16 現在**

```text
Usage: rfc-chronicle [OPTIONS] COMMAND [ARGS]...

  RFC-Chronicle CLI

Options:
  --help  Show this message and exit.

Commands:
  build-faiss     NumPy ベクトルから FAISS インデックスを生成 / 更新
  fetch           全 RFC のメタデータを取得し、必要なら本文ヘッダとマージして保存
  fulltext        SQLite FTS5 を使った全文検索
  index-fulltext  SQLite FTS5 全文検索 DB を再構築
  pin             RFC 番号をピン留め
  pins            ピン一覧を表示
  search          キャッシュ済みメタデータを条件で絞り込み
  semsearch       FAISS ベクトル検索（セマンティック検索）
  show            指定 RFC の詳細を表示・エクスポート
  unpin           ピンを解除
```