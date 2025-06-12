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
    """
    複数の条件（ステータス、日付範囲、キーワード）でRFCメタデータのリストをフィルタリングする。

    Args:
        rfcs       : フィルタ対象のRFCメタデータリスト
        statuses   : 絞り込み対象ステータス（Noneならフィルタなし）
        date_from  : 発行日 >= この日付（Noneなら下限なし）
        date_to    : 発行日 <= この日付（Noneなら上限なし）
        keyword    : タイトル、abstract、その他メタ情報に含まれる部分一致キーワード（Noneならフィルタなし）

    Returns:
        条件を満たすRfcMetadataオブジェクトのリスト
    """
    filtered: List[RfcMetadata] = []

    # ステータスの前処理：小文字化しておく
    normalized_statuses = {s.lower() for s in statuses} if statuses else None

    for rfc in rfcs:
        # ステータスフィルタ
        if normalized_statuses is not None:
            if rfc.status.lower() not in normalized_statuses:
                continue

        # 日付下限フィルタ
        if date_from is not None and rfc.date < date_from:
            continue

        # 日付上限フィルタ
        if date_to is not None and rfc.date > date_to:
            continue

        # キーワードフィルタ
        if keyword:
            kw = keyword.lower()
            # タイトル、abstract、モデルが提供する全テキストフィールドを結合して検索
            haystack = rfc.title.lower()
            if hasattr(rfc, 'abstract') and rfc.abstract:
                haystack += ' ' + rfc.abstract.lower()
            # 任意の追加メタデータ値も対象
            if hasattr(rfc, 'extra_metadata_values'):
                haystack += ' ' + ' '.join(str(v).lower() for v in rfc.extra_metadata_values())
            if kw not in haystack:
                continue

        filtered.append(rfc)

    return filtered
