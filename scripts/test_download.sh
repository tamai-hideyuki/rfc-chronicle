#!/usr/bin/env bash
set -euo pipefail

# まずシェルでメタデータ取得と表示
echo "=== Fetching metadata ==="
poetry run python - <<'PYCODE'
from rfc_chronicle.fetch_rfc import client
meta = client.fetch_metadata()
print(f"Example RFC number={meta[0]['number']} title={meta[0]['title']}")
PYCODE

# 次に本文ダウンロード部分を Python で
echo "=== Downloading RFC text ==="
poetry run python - <<'PYCODE'
from pathlib import Path
from rfc_chronicle.fetch_rfc import client

meta = client.fetch_metadata()
out_dir = Path("data/texts")
detail = client.fetch_details(meta[0], out_dir, use_conditional=False)
print(f"→ Downloaded to: {out_dir / (meta[0]['number'] + '.txt')}")
print("First 100 chars of body:")
print(detail["body"][:100].replace("\\n"," "))
PYCODE
