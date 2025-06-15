# 【M6-1】:

## RFC本文のダウンロード機能を実装する

**概要**
- 既存のメタデータ取得後に、各 RFC の本文テキストを `data/texts/{number}.txt` に保存
- URL テンプレート: `https://www.rfc-editor.org/rfc/rfc{number}.txt`
- 既存ファイルを常に上書きする仕様とする

**ToDo**
- `fetch_rfc.fetch_details` に本文取得ロジックを追加
- `save_path.write_text(..., encoding="utf-8")` で上書き保存
- （オプション）HTTP ヘッダの `ETag`/`Last-Modified` を読み取り → 変更時のみダウンロード
- ダウンロード失敗時のリトライ・エラーハンドリング
- 保存先ディレクトリを自動生成
- 単体テストを追加

---

## SQLite FTS5 を用いた全文検索 DB を構築する

**概要**
- `data/fulltext.db` に FTS5 テーブルを作成
- メタデータ（RFC番号・タイトル）と本文を格納
- `INSERT OR REPLACE` による差分更新方式を採用

**ToDo**
- `index_fulltext.py` を新規作成
- `sqlite-utils` で FTS5 テーブル (`rfc_text`) を作成
- `INSERT OR REPLACE` 文で既存行を更新
- `metadata.json` と `data/texts/*.txt` を一括取り込み
- スクリプトを Makefile や CLI サブコマンド化

<details>
<summary>メモ</summary>

poetry run rfc-chronicle fetch --save

poetry run rfc-chronicle index-fulltext

</details>

---

## CLI コマンド fulltext を追加する

**概要**
- SQLite FTS5 に対してクエリを投げ、マッチした RFC番号・タイトル・スニペットを表示
- バックエンド DB (`fulltext.db`) は毎回最新のファイルを開く

**ToDo**
- `rfc-chronicle fulltext <キーワード>` コマンド実装
- `snippet(...)` 関数でマッチ前後を抜粋表示
- オプションで件数指定（`--limit`）を追加
- CIテスト：DB再構築後も最新内容を返すことを検証

<details>
<summary>メモ</summary>

- メタデータを取得して ./data/metadata.json に保存  
poetry run rfc-chronicle fetch --save
  

- RFC1〜N をまとめてダウンロード（既存上書き）  
poetry run rfc-chronicle semfetch 1 10
  

- 全文検索DBを構築  
poetry run rfc-chronicle index-fulltext

</details>

### 運用方針：
- まず一括 DL: 
  - `./scripts/download_all.sh`
    - これで ./data/texts/0001.txt～./data/texts/NNNN.txt までをまとめて取得
      - 新しい RFC が増えたら、同じスクリプトを再実行

- ヘッダ＋本文情報を含むメタデータ生成
  - ダウンロードが完了したら、
    - `poetry run rfc-chronicle fetch --save`
    - これの実行で./data/metadata.json にヘッダ（Author, Date, …）と本文抜粋をマージした「詳細メタデータ」を書き出す

- 全文検索 DB の再構築
  - `poetry run rfc-chronicle index-fulltext`
    - ./data/fulltext.db に取得したすべてのドキュメントがインデックスされる



---

# 【M6-2】:

## ドキュメント単位 Embedding のバッチ処理を実装する

**概要**
- `sentence-transformers` モデル（all-MiniLM-L6-v2）で全文をエンコード
- 結果を `data/vectors.npy`、マッピングを `data/docmap.json` に保存
- 再実行時は常に上書き保存

**ToDo**
- `scripts/build_embeddings.py` を新規作成
- モデルロード → 一括エンコード → `.npy` で上書き保存
- RFC番号とインデックスのマップを作成
- メモリ管理／大規模データ対応の確認
- （オプション）差分追加対応：「既存配列読み込み → 新規分を concat → 上書き保存」

**scripts/build_embeddings.py 作成後**

```bash
# venv に NumPy を入れる

python3 -m venv .venv

source .venv/bin/activate

pip install numpy sentence-transformers torch tqdm

pip install matplotlib

chmod +x scripts/build_embeddings.py

# スクリプト実行例
./scripts/build_embeddings.py \
  --textdir data/texts \       # 読み込む *.txt を置いたディレクトリ
  --out-vect data/vectors.npy \# 出力する埋め込みベクトルファイル
  --out-map  data/docmap.json \# 出力する RFC 番号→行マップ
  --batch   32                 # １バッチあたりのファイル数


# オプション例：バッチサイズを小さくしてさらに低負荷に
./scripts/build_embeddings.py --batch 16
```

**これが実装できるとできること**
- 「意味的検索」「類似度計算」「クラスタリング・可視化」などを行えます。

**使用例**

- Semantic Search
```bash
# RFC123 に意味的に近い上位 5 件を表示

python3 scripts/analyze_embeddings.py search 123 --topk 5 
```

  
- Similarity
```bash
# RFC123 と RFC456 間のコサイン類似度＆ユークリッド距離を表示

python3 scripts/analyze_embeddings.py sim 123 456
```
  
- Clustering & Visualization
```bash
# 全 9588 件を 8 クラスターに分け、t-SNE で 2 次元プロット
 
python3 scripts/analyze_embeddings.py cluster --k 8
```



---

## FAISS インデックスを生成・保存する

**概要**
- `data/vectors.npy` から FAISS の `IndexFlatL2` を生成
- `data/faiss_index.bin` にシリアライズ保存
- 再実行時は常に上書き保存

**ToDo**
- `scripts/build_faiss_index.py` を新規作成
- NumPy から読み込み → FAISS で `add()` → `write_index()`
- 差分追加運用オプション：「既存インデックス読み込み → `add()` → 上書き保存」
- 将来的なインデックスタイプ切替設計（Flat, IVF, HNSW）
- ユニットテスト追加

**テスト**
```bash
pytest tests/test_build_faiss_index.py -q

poetry run pytest tests/test_build_faiss_index.py -q
```

**FAISS ビルド機能動作確認**
```bash
# Flat インデックス生成
poetry run rfc-chronicle build-faiss

# IVF インデックス生成
poetry run rfc-chronicle build-faiss --type ivf

# HNSW インデックス生成
poetry run rfc-chronicle build-faiss --type hnsw

# 更新モード
poetry run rfc-chronicle build-faiss -u --vectors data/new_vectors.npy


```

---

## CLI コマンド semsearch を追加する

**概要**
- 入力クエリをモデルでエンコード → FAISS 検索 → 上位N件を表示
- 常に最新の `faiss_index.bin` と `vectors.npy` を読み込む

**ToDo**
- `rfc-chronicle semsearch <クエリ>` 実装
- クエリエンコード最適化（キャッシュ、バッチ等）
- `--top N` オプション追加
- CIテスト：インデックス更新後も最新結果を返すことを検証

---

## ドキュメントに検索機能の使い方を追記する

**概要**
- README／docsに `fulltext`／`semsearch` の利用例・インストール手順を追加
- 本文・インデックス更新後は各スクリプト／コマンドを再実行する旨の注意書き
- 実行順序例を「① fetch → ② index_fulltext → ③ build_embeddings → ④ build_faiss_index → ⑤ fulltext/semsearch」と明示

**ToDo**
- 各コマンド説明セクション作成
- 前提条件・必要ライブラリの記載
- サンプル出力例の挿入（ログ／スクリーンショット等）  
