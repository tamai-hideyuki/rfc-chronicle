import pytest
from rfc_chronicle.fetch_rfc import fetch_metadata
from rfc_chronicle.utils import META_FILE
from pathlib import Path

def mock_response_html():
    # minimal HTML with required table structure
    return '''
    <html><body>
    <table></table><table></table>
    <table>
      <tr><td>1</td><td>Title A</td><td>January 2020</td><td>StatusA</td><td>Extra</td><td>Ignore</td><td>Active</td></tr>
      <tr><td>2</td><td>Title B</td><td>February 2021</td><td>StatusB</td><td>Extra</td><td>Ignore</td><td>Deprecated</td></tr>
    </table>
    </body></html>
    '''

class DummyResp:
    def __init__(self, text): self.text = text
    def raise_for_status(self): pass

@pytest.fixture(autouse=True)
def patch_requests(monkeypatch):
    monkeypatch.setattr('requests.get', lambda url: DummyResp(mock_response_html()))

@pytest.fixture
def tmp_meta(tmp_path, monkeypatch):
    path = tmp_path / 'metadata.json'
    monkeypatch.setattr('rfc_chronicle.fetch_rfc.META_FILE', path)
    return path


def test_fetch_metadata_list(tmp_meta):
    data = fetch_metadata(save=False)
    assert isinstance(data, list)
    assert data[0]['number'] == '1'
    assert data[0]['status'] == 'Active'


def test_fetch_metadata_save(tmp_meta):
    data = fetch_metadata(save=True)
    assert tmp_meta.exists()
    loaded = json.loads(tmp_meta.read_text(encoding='utf-8'))
    assert isinstance(loaded, list)
