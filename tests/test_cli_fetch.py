import pytest
from click.testing import CliRunner
from rfc_chronicle.cli import fetch
from rfc_chronicle.models import RfcMetadata
from rfc_chronicle.search import filter_rfcs

# モック用: load_all_rfcs を置き換える
import rfc_chronicle.cli as cli_module

@pytest.fixture(autouse=True)
def mock_load_all_rfcs(monkeypatch):
    rfcs = [
        RfcMetadata('1', 'First', 'draft', date(2021, 1, 1)),
        RfcMetadata('2', 'Second http', 'active', date(2021, 1, 10)),
        RfcMetadata('3', 'Third', 'draft', date(2021, 2, 1)),
    ]
    monkeypatch.setattr(cli_module, 'load_all_rfcs', lambda: rfcs)

from datetime import date

def test_fetch_no_filters_outputs_all(monkeypatch):
    runner = CliRunner()
    result = runner.invoke(fetch, [])
    assert result.exit_code == 0
    # 全3件出力される
    lines = [l for l in result.output.splitlines() if l.strip()]
    assert len(lines) == 3

def test_fetch_status_filter(monkeypatch):
    runner = CliRunner()
    result = runner.invoke(fetch, ['--status', 'draft'])
    assert result.exit_code == 0
    lines = [l for l in result.output.splitlines() if l.strip()]
    # draft は id 1,3
    assert len(lines) == 2
    assert lines[0].startswith('1\t') and lines[1].startswith('3\t')

def test_fetch_date_and_keyword(monkeypatch):
    runner = CliRunner()
    result = runner.invoke(fetch, [
        '--from', '2021-01-05',
        '--keyword', 'http'
    ])
    assert result.exit_code == 0
    lines = [l for l in result.output.splitlines() if l.strip()]
    # id 2 のみ
    assert len(lines) == 1 and lines[0].startswith('2\t')

def test_fetch_no_match(monkeypatch):
    runner = CliRunner()
    result = runner.invoke(fetch, ['--keyword', 'nomatch'])
    assert result.exit_code == 0
    assert 'No RFCs match the given criteria.' in result.output
