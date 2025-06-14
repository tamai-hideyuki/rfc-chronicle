#!/usr/bin/env bash
set -euo pipefail

echo "=== Downloading RFC1 to RFC10 (skipping 404) ==="
poetry run python - <<'PYCODE'
from pathlib import Path
from requests.exceptions import HTTPError
from rfc_chronicle.fetch_rfc import client

# 取得範囲をここで指定
START, END = 1, 10

# 一度だけメタデータを取得
meta_list = client.fetch_metadata()

out_dir = Path("data/texts")
out_dir.mkdir(parents=True, exist_ok=True)

for i in range(START, END + 1):
    num_str = f"{i:04d}"
    print(f"RFC{num_str} ... ", end="")

    # metadata に対応するエントリを探す
    try:
        meta = next(
            m for m in meta_list
            if client._normalize_number(m["number"]) == i
        )
    except StopIteration:
        print("No metadata, skipped")
        continue

    # ダウンロード＆404 スキップ
    try:
        client.fetch_details(meta, out_dir, use_conditional=False)
        print("OK")
    except HTTPError as e:
        if e.response.status_code == 404:
            print("Not Found, skipped")
        else:
            raise
PYCODE
