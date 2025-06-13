# M4: 詳細表示 & エクスポート 実装計画

- **rfc-chronicle に詳細表示とエクスポート機能を追加します。以下の項目ごとに実装していきます。**

### 主な実装の流れ

- fetch_details の実装
  - メタデータ取得に加え、RFC 本文をダウンロードする関数を実装
- フォーマッタ (formatters.py) の作成
  - SON/CSV/Markdown 変換関数を実装
- show コマンド追加
  - cli.py に show <number> --output [json|csv|md] を追加
- テストの追加
  - tests/test_cli_show.py で各フォーマット出力を検証

---

### show コマンドの追加

###  詳細データの取得 (fetch_details)

### フォーマッタの実装

### テストの追加

---

### ToDo

- [ ] fetch_details の実装

- [ ] formatters.py の作成

- [ ] cli.py の show コマンドと --output オプション追加

- [ ] ユニットテストの実装と CI への組み込み

---

### 実装後

```text
# 依存が最新か確認
poetry install

# すべてのテストを実行
poetry run pytest -q

# あるいは、show コマンドに限定してテスト
poetry run pytest tests/test_cli_show.py -q

# 次に実装した CLI コマンド自体を手動で動かしてみます。たとえば RFC 791
poetry run rfc-chronicle show 791

# JSON や CSV 出力を確認したいときは：
poetry run rfc-chronicle show 791 --output json
poetry run rfc-chronicle show 791 --output csv

```
