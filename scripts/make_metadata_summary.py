#!/usr/bin/env python3

import json
from pathlib import Path

# 元ファイル
src = Path("../data/metadata.json")
# 出力ファイル
dst = Path("../web-ui/data/metadata_summary.json")

with src.open(encoding="utf-8") as f:
    full = json.load(f)

# number と title だけ取り出す
summary = [
    {
        "number": item["number"],
        "title": item["title"],
    }
    for item in full
]

dst.parent.mkdir(parents=True, exist_ok=True)
with dst.open("w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
