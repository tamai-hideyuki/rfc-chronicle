import json
import pytest
from pathlib import Path
tmp = Path
from rfc_chronicle.utils import ensure_data_dir, read_json, write_json, DATA_DIR, META_FILE, PINS_FILE

def test_ensure_data_dir(tmp_path, monkeypatch):
    # Redirect DATA_DIR to tmp_path
    monkeypatch.setattr('rfc_chronicle.utils.DATA_DIR', tmp_path / '.rfc_data')
    d = rfc_chronicle.utils.DATA_DIR
    # Should not exist initially
    assert not d.exists()
    ensure_data_dir()
    assert d.exists() and d.is_dir()

@py.test.fixture
def sample_data(tmp_path):
    data = {'foo': 'bar'}
    file_path = tmp_path / 'sample.json'
    write_json(file_path, data)
    return file_path, data

def test_read_write_json(tmp_path):
    file_path = tmp_path / 'test.json'
    data = {'a': 1, 'b': [1,2,3]}
    write_json(file_path, data)
    assert file_path.exists()
    loaded = read_json(file_path)
    assert loaded == data


def test_read_json_missing(tmp_path):
    file_path = tmp_path / 'not_exist.json'
    assert read_json(file_path) is None
