import pytest
from click.testing import CliRunner
from rfc_chronicle.cli import show

# テスト用ダミーデータ
DUMMY_DETAILS = {
    'number': 123,
    'title': 'Test RFC',
    'date': '2025-06-13',
    'status': 'Informational',
    'body': 'This is a test body.'
}

@pytest.fixture(autouse=True)
def patch_fetch(monkeypatch):
    # fetch_details をモックし常に DUMMY_DETAILS を返す
    monkeypatch.setattr('rfc_chronicle.cli.fetch_details', lambda n: DUMMY_DETAILS)
    return monkeypatch

@pytest.mark.parametrize("output, expected_snippet", [
    ('json', '"number": 123'),
    ('csv', 'number,123'),
    ('md', '# RFC 123: Test RFC')
])
def test_show_formats(output, expected_snippet):
    runner = CliRunner()
    result = runner.invoke(show, ['123', '--output', output])
    assert result.exit_code == 0
    assert expected_snippet in result.output


def test_show_missing_number():
    runner = CliRunner()
    result = runner.invoke(show, [])
    assert result.exit_code != 0
    assert 'Error' in result.output
