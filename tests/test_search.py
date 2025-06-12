from datetime import date
from typing import Any, Dict, List, Optional

class RfcMetadata:
    """
    RFCメタデータを保持するモデルクラス。

    Attributes:
      id       : RFC番号やID
      title    : RFCのタイトル
      status   : RFCのステータス
      date     : 発行日
      abstract : 概要（任意）
      _extra   : その他のメタデータを辞書形式で保持
    """
    def __init__(
        self,
        id: str,
        title: str,
        status: str,
        date: date,
        abstract: Optional[str] = None,
        **extra: Any,
    ):
        self.id = id
        self.title = title
        self.status = status
        self.date = date
        self.abstract = abstract
        self._extra: Dict[str, Any] = extra or {}

    def extra_metadata_values(self) -> List[str]:
        """
        追加メタデータの値を文字列表現にしてリストで返す。
        """
        return [str(v) for v in self._extra.values()]

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RfcMetadata):
            return False
        return (
            self.id == other.id and
            self.title == other.title and
            self.status == other.status and
            self.date == other.date and
            self.abstract == other.abstract and
            self._extra == other._extra
        )

    def __repr__(self) -> str:
        return (
            f"RfcMetadata(id={self.id!r}, title={self.title!r}, status={self.status!r}, "
            f"date={self.date!r}, abstract={self.abstract!r}, extra={self._extra!r})"
        )
