from datetime import date
from typing import List, Optional
from .models import RfcMetadata

def filter_rfcs(
    rfcs: List[RfcMetadata],
    statuses: Optional[List[str]] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    keyword: Optional[str] = None,
) -> List[RfcMetadata]:
    normalized_statuses = {s.lower() for s in statuses} if statuses else None
    filtered: List[RfcMetadata] = []

    for rfc in rfcs:
        if normalized_statuses is not None and rfc.status.lower() not in normalized_statuses:
            continue
        if date_from and rfc.date < date_from:
            continue
        if date_to   and rfc.date > date_to:
            continue
        if keyword:
            kw = keyword.lower()
            haystack = rfc.title.lower()
            if rfc.abstract:
                haystack += ' ' + rfc.abstract.lower()
            haystack += ' ' + ' '.join(rfc.extra_metadata_values())
            if kw not in haystack:
                continue
        filtered.append(rfc)

    return filtered
