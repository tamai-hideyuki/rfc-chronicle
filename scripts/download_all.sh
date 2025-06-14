#!/usr/bin/env bash
set -euo pipefail

echo "=== Downloading all known RFCs (skipping missing) ==="
poetry run python - <<'PYCODE'
from pathlib import Path
from requests.exceptions import HTTPError
from rfc_chronicle.fetch_rfc import client

# 1) 一度だけメタデータ一覧を取得
meta_list = client.fetch_metadata()

# 2) 最大番号を計算
nums = [client._normalize_number(m["number"]) for m in meta_list]
max_num = max(nums)

out_dir = Path("data/texts")
out_dir.mkdir(parents=True, exist_ok=True)

# 3) 1 から max_num までループ
for i in range(1, max_num + 1):
    num_str = f"{i:04d}"
    print(f"RFC{num_str} ... ", end="")

    # メタデータに存在しない番号はスキップ
    if i not in nums:
        print("No metadata, skipped")
        continue

    meta = next(m for m in meta_list if client._normalize_number(m["number"]) == i)

    # ダウンロード＆404スキップ
    try:
        client.fetch_details(meta, out_dir, use_conditional=False)
        print("OK")
    except HTTPError as e:
        if e.response.status_code == 404:
            print("Not Found, skipped")
        else:
            raise
PYCODE
