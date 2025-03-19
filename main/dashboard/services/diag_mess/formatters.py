from typing import Iterable
from dataclasses import dataclass


@dataclass
class DiagMessRecord:
    asset_id: int = None
    asset_type: str = ""
    asset_name: str = ""
    timestamp: str = None
    message: str = ""
    group: str = None
    level_code: str = None
    unused_filed: str = None
    id_tab: str = None,
    signals: str = None

    @classmethod
    def from_raw_record(cls, *args):
        if len(args) >= 10:
            return DiagMessRecord(*args[:10])
        else:
            return None


def to_subst_page(diags: Iterable[dict], count_diags):
    """Возвращает диаг. сообщения для отображения
    на странице подстанции"""
    if diags is None:
        diags = []
    return {
        "diag_messages": [
            {
                "asset": rec.get("asset_name"),
                "asset_id": rec.get("asset"),
                "asset_type": rec.get("asset_type"),
                "type": rec.get("group"),
                "timestamp": rec.get("time"),
                "_time": rec.get("_time"),
                "message": rec.get("message"),
                "level": rec.get("level"),
                "id_tab": rec.get("id_tab"),
                "signals": rec.get("signals"),
            }
            for rec in diags
        ],
        "count_messages": count_diags
    }
