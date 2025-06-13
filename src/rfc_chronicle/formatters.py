import json
from io import StringIO
import csv

def format_json(details):
    return json.dumps(details, ensure_ascii=False, indent=2)

def format_csv(details):
    output = StringIO()
    writer = csv.writer(output)
    # 単純なキーと値の二段テーブル
    for k, v in details.items():
        writer.writerow([k, v])
    return output.getvalue()

def format_md(details):
    md = []
    md.append(f"# RFC {details['number']}: {details['title']}")
    md.append(f"**Date:** {details['date']}")
    md.append(f"**Status:** {details['status']}")
    md.append("---")
    md.append(details['body'])
    return '\n\n'.join(md)
