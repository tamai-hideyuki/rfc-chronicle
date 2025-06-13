import json
import csv
from io import StringIO
from typing import Dict, Any


def format_json(details: Dict[str, Any]) -> str:
    """辞書を JSON 文字列へ整形"""
    return json.dumps(details, ensure_ascii=False, indent=2)


def format_csv(details: Dict[str, Any]) -> str:
    """辞書を CSV (key,value) 形式へ整形"""
    output = StringIO()
    writer = csv.writer(output)
    for k, v in details.items():
        writer.writerow([k, v])
    return output.getvalue()


def format_md(records):
    """
    レコードのリストを Markdown の表形式に整形して返す
    """
    if not records:
        return ""
    headers = records[0].keys()
    # ヘッダ行
    md = "| " + " | ".join(headers) + " |\n"
    md += "| " + " | ".join("---" for _ in headers) + " |\n"
    # 各レコード
    for rec in records:
        md += "| " + " | ".join(str(rec[h]) for h in headers) + " |\n"
    return md


__all__ = ["format_json", "format_csv", "format_md"]
