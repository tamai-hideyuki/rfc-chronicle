import pytest
from click.testing import CliRunner
from rfc_chronicle.cli import cli
from pathlib import Path

def test_fetch_command(monkeypatch, tmp_path):
    # patch fetch_metadata
    monkeypatch.setattr('rfc_chronicle.fetch_rfc.fetch_metadata', lambda save: [{'number':'1'}])
    # patch META_FILE
    from rfc_chronicle.utils import META_FILE
    monkeypatch.setattr('rfc_chronicle.utils.META_FILE', tmp_path/'metadata.json')
    runner = CliRunner()
    result = runner.invoke(cli, ['fetch'])
    assert result.exit_code == 0
    assert 'Saved 1 RFC entries' in result.output


def test_search_command(monkeypatch, tmp_path):
    # prepare cache file
    meta = tmp_path/'metadata.json'
    content = [{'number':'1','title':'Test','date':'January 2020','status':'Active'}]
    meta.write_text(json.dumps(content), encoding='utf-8')
    monkeypatch.setattr('rfc_chronicle.utils.META_FILE', meta)
    runner = CliRunner()
    result = runner.invoke(cli, ['search', '--from-date', '2020', '--to-date', '2020', '--keyword', 'Test'])
    assert result.exit_code == 0
    assert 'Matched RFC 1' in result.output
    assert 'RFC 1: Test' in result.output
