from datetime import date
from rfc_chronicle.search import filter_rfcs
from rfc_chronicle.models import RfcMetadata

def make_rfc(id, title, status, dt, abstract=None, **extra):
    return RfcMetadata(id=id, title=title, status=status,
                       date=dt, abstract=abstract, **extra)

def test_no_filters_returns_all():
    rfcs = [
        make_rfc('1', 'First', 'draft', date(2021, 1, 1)),
        make_rfc('2', 'Second', 'active', date(2021, 2, 1)),
    ]
    assert filter_rfcs(rfcs) == rfcs

# …and the rest of your test_* functions…
