import pytest
from pathlib import Path
from rfc_chronicle import utils


def test_ensure_data_dir(tmp_path, monkeypatch):
    # DATA_DIR を一時ディレクトリに差し替え
    monkeypatch.setattr(utils, 'DATA_DIR', tmp_path / '.rfc_data')
    d = utils.DATA_DIR
    assert not d.exists()
    utils.ensure_data_dir()
    assert d.exists() and d.is_dir()


def test_read_write_json(tmp_path):
    file_path = tmp_path / 'test.json'
    data = {'a': 1, 'b': [1, 2, 3]}
    utils.write_json(file_path, data)
    assert file_path.exists()
    loaded = utils.read_json(file_path)
    assert loaded == data


def test_read_json_missing(tmp_path):
    file_path = tmp_path / 'not_exist.json'
    assert utils.read_json(file_path) is None
