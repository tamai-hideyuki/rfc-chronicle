# インタラクティブシェルの使い方

**rfc-chronicle shell コマンドで起動する対話型シェルでは、以下のコマンドを利用できます。**

## 起動方法

```bash
# 仮想環境内または poetry run 経由で実行
poetry run rfc-chronicle shell
```
- プロンプトが表示されます。

```bash
Welcome to RFC Chronicle Shell. Type help or ? to list commands.
>
```
## コマンド一覧

|コマンド| 説明 | 例                          |
|---|---|----------------------------|
|fetch|RFC メタデータを全件取得して保存| > fetch                    |
|build_faiss|FAISS インデックスを（再）構築| > build_faiss              |
|fulltext <キーワード>|FTS5 による全文検索| > fulltext OAuth           |
|index_fulltext|FTS5 の全文インデックスを再作成| > index_fulltext           |
|search <クエリ>|メタデータ検索（タイトルやステータスなど）| > search TLS               |
|semsearch <クエリ>|ベクトル検索による類似 RFC 検索（スコア, RFC 番号）| > semsearch HTTP           |
|pin <番号>|RFC をピンに追加| > pin 7151                 |
|unpin <番号>|ピンから RFC を削除| > unpin 7151               |
|pins|現在ピンしている RFC 一覧を表示| > pins                     |
|show <番号> [--format]|RFC 詳細を表示／エクスポート（format: md, json, csv）| > show 959 --format=json   |
|exit|シェルを終了| > exit                     |


## 使い方の流れ例

### 1. メタデータ取得
```bash
> fetch
```

### 2. 全文インデックス再構築
```bash
> index_fulltext
```

### 3. FAISS インデックス構築
```bash
> build_faiss
```

### 4. メタデータ検索
```bash
> search DNS
```

### 5. ベクトル検索
```bash
> semsearch Virtual
```

### 6. 気になる RFC をピン
```bash
> pin 7151
```

### 7. ピン一覧確認
```bash
> pins
```

### 8. RFC 詳細表示／エクスポート
```bash
> show 7151 --format=md
```

### 9. 終了
```bash
> exit
```


## ヘルプ
### シェル上で help または ? を入力すると、すべてのコマンド一覧と簡易説明が表示されます。
```bash
```

> help