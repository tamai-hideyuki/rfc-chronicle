import json
import pytest
from click.testing import CliRunner
from rfc_chronicle.cli import cli
from rfc_chronicle import fetch_rfc, utils


def test_fetch_command(monkeypatch, tmp_path):
    # fetch_metadataをモックして1件返す
    monkeypatch.setattr(fetch_rfc, 'fetch_metadata', lambda save: [{'number': '1'}])
    # META_FILEを一時ファイルに差し替え
    monkeypatch.setattr(utils, 'META_FILE', tmp_path / 'metadata.json')

    runner = CliRunner()
    result = runner.invoke(cli, ['fetch'])
    assert result.exit_code == 0
    assert 'Saved 1 RFC entries' in result.output


def test_search_command(monkeypatch, tmp_path):
    # キャッシュファイルにサンプルデータを書き込み
    meta_file = tmp_path / 'metadata.json'
    content = [{'number': '1', 'title': 'Test', 'date': 'January 2020', 'status': 'Active'}]
    meta_file.write_text(json.dumps(content), encoding='utf-8')
    monkeypatch.setattr(utils, 'META_FILE', meta_file)

    runner = CliRunner()
    result = runner.invoke(cli, ['search', '--from-date', '2020', '--to-date', '2020', '--keyword', 'Test'])
    assert result.exit_code == 0
    assert 'Matched RFC 1' in result.output
    assert 'RFC 1: Test' in result.output
