### 要件整理と設計
– フィルタ項目の網羅性（例：ステータス大文字・小文字の許容、キーワード検索対象フィールドの明確化）
– 日付フォーマット不正時のエラーハンドリング

<details>
<summary>詳細</summary>

## フィルタ項目

| フィルタ名       | 説明                              | 型           | 補足                     |
| ----------- | ------------------------------- | ----------- | ---------------------- |
| `status`    | RFCのステータス（例：`draft`／`active`など） | `List[str]` | 大文字小文字を区別せずにマッチさせる     |
| `date_from` | 日付範囲の開始（inclusive）              | `date`      | YYYY-MM-DD形式。未指定時は制限なし |
| `date_to`   | 日付範囲の終了（inclusive）              | `date`      | YYYY-MM-DD形式。未指定時は制限なし |
| `keyword`   | タイトル・概要・その他メタデータ内テキスト検索         | `str`       | 部分一致。未指定時は制限なし         |


## CLIオプション設計

```bash
rfc fetch \
  [--status STATUS[,STATUS…]] \
  [--from YYYY-MM-DD] \
  [--to   YYYY-MM-DD] \
  [--keyword KEYWORD]
```
- --status, -s
  - カンマ区切り or 複数指定（Clickのmultiple=True or コールバックでリスト化）
  - 例：--status draft --status active あるいは --status draft,active

- --from
  - YYYY-MM-DD形式。パースに失敗したらエラー退出

- --to
  - YYYY-MM-DD形式。パースに失敗したらエラー退出

- --keyword, -k
  - シンプルな文字列。シェルでの引用に注意

## search.py の API設計

- 型ヒントとdocstringを徹底し、後で自動生成ドキュメントにも流用可能に
- 内部で使う比較ロジックはプライベート関数化してテストしやすくする

## ユーティリティ・設計メモ

- 日付パース関数
  - ステータス正規化
  - フィルタ前に全て小文字化しておく

- キーワード検索対象の拡張
  - RfcMetadat

## エラーハンドリング

- CLIレイヤーでのバリデーション失敗時は click.UsageError を投げて適切にユーザーに通知
- filter_rfcs内部では引数チェック不要（型保証は呼び出し元が担保）

## テスト設計

- モックデータ用ヘルパー
- テストケース一覧
  - ステータスフィルタ単体テスト
  - 日付レンジ（fromのみ／toのみ／両指定）
  - キーワードフィルタ（タイトル／abstract／extra_metadata）
  - 複数条件のAND組み合わせ
  - Noneや空リスト指定時に全件返却
  - 境界条件（日付 == from／to）

- CLIヘルプ出力確認

```bash
pytest --capture=tee-sys tests/test_cli.py::test_fetch_help
```

## 動作確認

```bash
# draftかつ2025-01-01〜2025-06-30に発行され、本文やタイトルに"http"を含むRFCを取得
rfc fetch \
  --status draft \
  --from 2025-01-01 \
  --to   2025-06-30 \
  --keyword http
```
- 実際のRFCメタデータを用いた手動確認
- CIでは上記に相当するpytestケースを自動実行




</details>

### CLIオプション
– --status draft,active のようなカンマ区切り／繰り返し指定（multiple=True）どちらを採用するか統一
– --from／--to が未指定の場合の挙動を明文化

### search.py の API
– 型ヒントとドキュメンテーション文字列（docstring）を充実させておくと、後からの拡張が楽になります

### CLIオプションの追加
– Click ならば multiple=True もしくはカスタムコールバックでリスト化
– 変換ロジックはユーティリティ関数にまとめるとテストしやすい

### 検索ロジック実装
– フィルタリング条件は順序を入れ替えて早期リターン（False）させるとパフォーマンス向上
– キーワード検索は将来的に正規表現や全文検索への置き換えを想定してインターフェース化すると良い

### テストケース追加
– 境界値（date_from == r.date、date_to == r.date）の確認
– 空リストや None 指定時にフィルタが適用されないことの確認
– 複数ステータス、複数キーワード（部分一致 vs 完全一致）のケース

<details>
<summary>test_search.py</summary>
poetry run pytest tests/test_search.py


</details>

### 動作確認
– 実際のRFCデータセットを用いた手動確認
– CIではテストのみならず、CLIのヘルプ表示（--help）もチェック

