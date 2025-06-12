- **もしまだ pytest が dev グループに入っていない場合は、以下で追加してから実行**

```bash
poetry add --group dev pytest
```
---

# プロジェクト全体のテストを一括実行

```bash
poetry run pytest
```

---

## test_utils.py

```bash
poetry run pytest tests/test_utils.py
```

## test_fetch_rfc.py

```bash
poetry run pytest tests/test_fetch_rfc.py
```

## test_cli.py

```bash
poetry run pytest tests/test_cli.py
```

---

## 詳細な出力で実行

```bash
poetry run pytest -v
```

---

### テストまとめ

```bash
poetry run pytest        # 全部のテストを一括実行

poetry run pytest -v     # 詳細出力

poetry run pytest tests   # testsディレクトリ配下のみ
```