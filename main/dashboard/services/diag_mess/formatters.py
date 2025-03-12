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


def to_subst_page(diags: Iterable[tuple], count_diags):
    """Возвращает диаг. сообщения для отображения
    на странице подстанции"""
    if diags is None:
        diags = []
    return {
        "diag_messages": [
            {
                "asset": mess.asset_name,
                "asset_id": mess.asset_id,
                "asset_type": mess.asset_type,
                "type": mess.group,
                "timestamp": mess.timestamp,
                "message": mess.message,
                "level": mess.level_code,
                "id_tab": mess.id_tab,
                "signals": mess.signals,
            }
            for rec in diags if (mess := DiagMessRecord.from_raw_record(*rec))
        ],
        "count_messages": count_diags
    }
