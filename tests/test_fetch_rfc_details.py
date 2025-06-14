import pytest
from pathlib import Path
from requests.models import Response
from rfc_chronicle.fetch_rfc import RFCClient

class DummyResponse(Response):
    def __init__(self, status_code:int, text:str=""):
        super().__init__()
        self._content = text.encode()
        self.status_code = status_code

class DummySession:
    def __init__(self, responses):
        self._it = iter(responses)
    def get(self, url, headers=None):
        return next(self._it)

@pytest.fixture
def tmp_text_dir(tmp_path):
    return tmp_path / "texts"

def test_fetch_details_overwrite(tmp_text_dir, monkeypatch):
    # 初回取得: 200, "first"
    # 再取得: 200, "second"
    client = RFCClient()
    client.session = DummySession([
        DummyResponse(200, "first content"),
        DummyResponse(200, "second content"),
    ])
    metadata = {"rfc_number": "0001"}
    # 初回
    text1 = client.fetch_details(metadata, tmp_text_dir)
    assert (tmp_text_dir / "0001.txt").read_text() == "first content"
    # 再実行（上書き）
    text2 = client.fetch_details(metadata, tmp_text_dir)
    assert (tmp_text_dir / "0001.txt").read_text() == "second content"

def test_fetch_details_conditional_not_modified(tmp_text_dir, monkeypatch):
    # 初回: 200, "foo"
    # 304: no overwrite
    client = RFCClient()
    client.session = DummySession([
        DummyResponse(200, "foo"),
        DummyResponse(304, ""),
    ])
    metadata = {"rfc_number": "0002"}
    client.fetch_details(metadata, tmp_text_dir, use_conditional=True)
    # ファイルは "foo"
    assert (tmp_text_dir / "0002.txt").read_text() == "foo"
    client.fetch_details(metadata, tmp_text_dir, use_conditional=True)
    # 変更なし → そのまま
    assert (tmp_text_dir / "0002.txt").read_text() == "foo"
