# 名称：「rfc-chronicle」

**rfc-chronicle は、RFC-Editor から膨大な RFC ドキュメントをサクッとローカルに取り込み、  
キーワード検索もベクトル検索も一気通貫でこなせる CLI ツールです。**

![PyPI version](https://img.shields.io/pypi/v/rfc-chronicle.svg)
![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)
![Poetry](https://img.shields.io/badge/poetry-1.5%2B-blue.svg)
![Click](https://img.shields.io/badge/click-8.1%2B-blue.svg)
![FAISS](https://img.shields.io/badge/faiss-enabled-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)

> Windows (native) でも Python 3.13+ と venv／Poetry 環境を整えれば動作しますが、  
> WSL2 上での動作を推奨しています。

---

## 前提条件：(macOS)

| ツール                   | 要件／備考                                                                                                                                           |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| **Zsh**                 | v4.3.9 以降で動作しますが、**v5.0.8 以降** を推奨。<br>`zsh --version` でバージョン確認可。                                                             |
| **curl** または **wget** | データ取得スクリプト（`download_all.sh` など）で使用。<br>どちらか一方があればOK。                                                                       |
| **git**                 | **v2.4.11 以上** を推奨。<br>`git --version` でバージョン確認可。                                                                                        |
| **Python**              | **3.13 以上** が必要。<br>`python3 --version` で確認。                                                                                                  |
| **Poetry**              | パッケージ管理に利用。<br>`poetry --version` で確認。<br>未インストール時は  
`\`curl -sSL https://install.python-poetry.org | python3 -\``                                                                              |
| **venv**                | 仮想環境を使う場合は標準の `venv` モジュールで OK。<br>`python3 -m venv --help` で確認。                                                                 |

**確認例**

```bash
zsh --version       # → zsh 5.8 (x86_64-apple-darwin20.1.0)
git --version       # → git version 2.39.1
python3 --version   # → Python 3.13.0
poetry --version    # → Poetry version 1.5.9
curl --version      # → curl 8.0.1 (x86_64-apple-darwin)
```

---

## 機能:
- メタデータ＆本文取得

- 全文検索 (FTS5)

- セマンティック検索

- 類似度計算

- クラスタリング＆可視化

- 詳細表示／ピン留め

---


## 使い方:
- **まずはリポジトリをクローンし、venv 環境下でセットアップします。**

```bash
# 1. clone
git clone https://github.com/tamai-hideyuki/rfc-chronicle.git

# 2. 仮想環境を作成＆有効化
cd rfc-chronicle
python3 -m venv .venv
source .venv/bin/activate

# 3. パッケージをインストール
pip install --upgrade pip
pip install .

# 4. CLI が使えるか確認
rfc-chronicle --help

# 5. 本文一括ダウンロード
# data/texts/ にすべての RFC 本文（123.txt 形式）が取得されます。
./scripts/download_all.sh

# 6. メタデータ＋本文情報を含む JSON 保存
# data/metadata.json にメタデータ＋本文ヘッダがまとめて保存されます。
poetry run rfc-chronicle fetch --save

# 7. 全文検索インデックス構築
# SQLite FTS5 を使った全文検索インデックスを作成します。
poetry run rfc-chronicle index-fulltext

```

# ここまでで以下の機能がアクティブになります!

```text
メタデータ＆本文取得 → ローカルにJSON/テキスト保存

全文検索 (FTS5) → rfc-chronicle fulltext <キーワード> --limit N でキーワード検索

詳細表示／ピン留め → rfc-chronicle show <RFC番号> / pin / pins / unpin

```

---

## セマンティック検索・類似度計算・クラスタリング＆可視化を有効化するにはこの先へ

上記までの手順で「メタデータ取得」「全文検索」「詳細表示／ピン留め」はすぐに使えます。  
続いて、以下を実行すると「セマンティック検索」「類似度計算」「クラスタリング＆可視化」機能もアクティブになります。

1. **埋め込みベクトルの生成**  
   全 RFC 本文をベクトル化し、`data/vectors.npy` と `data/docmap.json` を出力します。(初回は数分かかる場合があります。)
```bash
python3 scripts/build_embeddings.py \
 --textdir data/texts \
 --out-vect data/vectors.npy \
 --out-map  data/docmap.json \
 --batch   32
```
   
2. **セマンティック検索（意味的に近いRFCを探す）**
```bash
python3 scripts/analyze_embeddings.py search <RFC番号> --topk <件数> 

# 例：RFC123 に意味的に近い上位5件
python3 scripts/analyze_embeddings.py search 123 --topk 5
```

3. **類似度計算（2つのRFCの類似度を数値化）**
```bash
python3 scripts/analyze_embeddings.py sim <RFC番号1> <RFC番号2>

# 例：RFC123 と RFC456 のコサイン類似度＆ユークリッド距離
python3 scripts/analyze_embeddings.py sim 123 456
```

4. **クラスタリング＆可視化（全RFCをトピック別に散布図で把握）**
```bash
python3 scripts/analyze_embeddings.py cluster \
  --k <クラスタ数> \
  [--sample <サンプル件数>] \
  [--perplexity <値>]
  

# 例：8クラスター、t-SNE 用に2000件サンプルで可視化
python3 scripts/analyze_embeddings.py cluster \
  --k 8 \
  --sample 2000 \
  --perplexity 50 
```
