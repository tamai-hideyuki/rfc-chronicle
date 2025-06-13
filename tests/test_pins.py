import json
from pathlib import Path
import pytest
from click.testing import CliRunner

import rfc_chronicle.cli as cli_module
from rfc_chronicle.cli import cli

@pytest.fixture(autouse=True)
def temp_pins_file(monkeypatch, tmp_path):
    # Use a temporary pins file for each test
    temp_file = tmp_path / "pins.json"
    monkeypatch.setattr(cli_module, 'PINS_FILE', temp_file)
    yield


def test_load_pins_initial_empty():
    pins = cli_module.load_pins()
    assert pins == []
    # File should be created on load
    assert cli_module.PINS_FILE.exists()


def test_pin_and_save():
    runner = CliRunner()
    result = runner.invoke(cli, ['pin', '10'])
    assert result.exit_code == 0
    assert "RFC 10 をピンしました" in result.output
    data = json.loads(cli_module.PINS_FILE.read_text(encoding='utf-8'))
    assert data == [10]


def test_double_pin_no_duplicate():
    runner = CliRunner()
    runner.invoke(cli, ['pin', '5'])
    result = runner.invoke(cli, ['pin', '5'])
    assert "すでにピンされています" in result.output
    data = json.loads(cli_module.PINS_FILE.read_text(encoding='utf-8'))
    assert data == [5]


def test_unpin_and_remove():
    runner = CliRunner()
    runner.invoke(cli, ['pin', '3'])
    result = runner.invoke(cli, ['unpin', '3'])
    assert result.exit_code == 0
    assert "ピンを解除しました" in result.output
    data = json.loads(cli_module.PINS_FILE.read_text(encoding='utf-8'))
    assert data == []


def test_unpin_nonexistent():
    runner = CliRunner()
    result = runner.invoke(cli, ['unpin', '7'])
    assert "ピンされていません" in result.output


def test_list_show_pins_marker(monkeypatch):
    class Item:
        pass
    items = []
    for num, title in [(1, "A"), (2, "B")]:
        it = Item()
        it.number = num
        it.title = title
        items.append(it)
    monkeypatch.setattr(cli_module, 'fetch_metadata_list', lambda *args, **kwargs: items)
    runner = CliRunner()
    runner.invoke(cli, ['pin', '1'])
    result = runner.invoke(cli, ['list', '--show-pins'])
    assert '📌 RFC001' in result.output
    assert '   RFC002' in result.output


def test_list_pins_only(monkeypatch):
    class Item:
        pass
    items = []
    for num in [4, 5, 6]:
        it = Item()
        it.number = num
        it.title = f"T{num}"
        items.append(it)
    monkeypatch.setattr(cli_module, 'fetch_metadata_list', lambda *args, **kwargs: items)
    runner = CliRunner()
    runner.invoke(cli, ['pin', '4'])
    runner.invoke(cli, ['pin', '6'])
    result = runner.invoke(cli, ['list', '--pins-only'])
    lines = [l for l in result.output.splitlines() if l.strip()]
    assert all(('RFC004' in l or 'RFC006' in l) for l in lines)
