#!/usr/bin/env bash
set -euo pipefail

echo "=== Downloading RFC1 to RFC10 ==="
for i in {1..10}; do
  # 先頭をゼロパディング（例: 1→0001）
  num=$(printf "%04d" "$i")
  echo "Downloading RFC${num}..."
  poetry run python - <<PYCODE
from pathlib import Path
from rfc_chronicle.fetch_rfc import client

# メタデータ一覧をキャッシュ取得
meta_list = client.fetch_metadata()

# 指定番号の metadata を探す
meta = next(m for m in meta_list if m["number"] == "$num" or m.get("rfc_number") == "$num")
# ダウンロード＆保存
out = client.fetch_details(meta, Path("data/texts"), use_conditional=False)
print(f"  → saved to data/texts/{num}.txt")
PYCODE
done
