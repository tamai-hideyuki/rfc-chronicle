#!/usr/bin/env bash
set -euo pipefail

echo "=== Downloading RFC1 to RFC10 (skipping 404) ==="
for i in {1..30}; do
  num=$(printf "%04d" "$i")
  echo -n "RFC${num} ... "
  poetry run python - <<PYCODE
from pathlib import Path
from requests.exceptions import HTTPError
from rfc_chronicle.fetch_rfc import client

meta_list = client.fetch_metadata()
# 整数比較で該当メタデータだけ抽出
meta = next(m for m in meta_list if client._normalize_number(m["number"]) == $i)
out_dir = Path("data/texts")
try:
    client.fetch_details(meta, out_dir, use_conditional=False)
    print("OK")
except HTTPError as e:
    if e.response.status_code == 404:
        print("Not Found, skipped")
    else:
        raise
PYCODE
done
