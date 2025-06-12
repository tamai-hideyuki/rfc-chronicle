import json
import pytest
import requests
from rfc_chronicle.fetch_rfc import fetch_metadata


def mock_response_html():
    return '''
    <html><body>
    <table></table><table></table>
    <table>
      <tr><th>Number</th><th>Files</th><th>Title</th><th>Authors</th><th>Date</th><th>More Info</th><th>Status</th></tr>
      <tr><td>1</td><td>f</td><td>Title A</td><td>a</td><td>January 2020</td><td>i</td><td>Active</td></tr>
      <tr><td>2</td><td>f</td><td>Title B</td><td>b</td><td>February 2021</td><td>i</td><td>Deprecated</td></tr>
    </table>
    </body></html>
    '''

class DummyResp:
    def __init__(self, text):
        self.text = text
    def raise_for_status(self):
        pass

@pytest.fixture(autouse=True)
def patch_requests(monkeypatch):
    monkeypatch.setattr(requests, 'get', lambda url: DummyResp(mock_response_html()))

@pytest.fixture
def tmp_meta(tmp_path, monkeypatch):
    from rfc_chronicle.fetch_rfc import META_FILE
    meta_path = tmp_path / 'metadata.json'
    monkeypatch.setattr('rfc_chronicle.fetch_rfc.META_FILE', meta_path)
    return meta_path


def test_fetch_metadata_list(tmp_meta):
    data = fetch_metadata(save=False)
    assert isinstance(data, list)
    # 最初のデータは1
    assert data[0]['number'] == '1'
    assert data[1]['number'] == '2'


def test_fetch_metadata_save(tmp_meta):
    data = fetch_metadata(save=True)
    assert tmp_meta.exists()
    loaded = json.loads(tmp_meta.read_text(encoding='utf-8'))
    assert loaded == data

