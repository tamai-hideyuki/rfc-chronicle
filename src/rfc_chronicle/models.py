from datetime import date
from typing import Any, Dict, List, Optional

class RfcMetadata:
    def __init__(self, id: str, title: str, status: str, date: date,
                 abstract: Optional[str] = None, **extra: Any):
        self.id = id
        self.title = title
        self.status = status
        self.date = date
        self.abstract = abstract
        self._extra: Dict[str, Any] = extra or {}

    def extra_metadata_values(self) -> List[str]:
        return [str(v) for v in self._extra.values()]

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RfcMetadata):
            return False
        return (self.id == other.id and self.title == other.title and
                self.status == other.status and self.date == other.date and
                self.abstract == other.abstract and self._extra == other._extra)
