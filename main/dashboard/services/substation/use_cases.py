import logging
from asyncpg import Record as ApgRec
from copy import deepcopy
from typing import Dict, Iterable, List, Union

from dashboard.models import AssetsTypeChartTabs, Substations
from dashboard.services.commons.assets_manager import AssetsManager, AssetDesc
from dashboard.services.commons.conclusion_table_line import CONCLUS_TABLE_LINES
from dashboard.services.commons.meterings_manager import MeteringsManager
from dashboard.services.commons.signal_desc import SignalDesc
from dashboard.services.commons.status import get_status_name, txt_status_to_number100
from dashboard.services.meterings.formatters import get_meterings_by_codes
from dashboard.utils import time_func
from dashboard.utils.number import Numeric
from localization.services.translation.asset import AssetDescTralslation
from localization.services.translation.conclus_table import ConclusTableLineTralslation

from main.settings import ROUND_NDIGIT


logger = logging.getLogger(__name__)


def get_all_assets_with_statuses(lang: str):
    """Получить данные обо всем оборудовании с их статусами."""
    status_code = "condition"

    assets = AssetsManager.get_all()
    if assets:
        data, status = MeteringsManager.get_last_meterings(
            assets,
            (status_code,))
    else:
        data = []
        status = True
    asset_values = {}
    for record in data:
        if not isinstance(record, (list, tuple, ApgRec)) or len(record) < 3:
            continue
        asset_guid = record[0]
        if asset_guid not in asset_values:
            asset_values[asset_guid] = {}
        asset_values[asset_guid][status_code] = get_status_name(record[2])

    AssetDescTralslation.translate_collections([assets], lang)

    asset_by_subst = {}
    for asset in assets:
        if asset.subst_id not in asset_by_subst:
            asset_by_subst[asset.subst_id] = {}
            asset_by_subst[asset.subst_id]["id"] = asset.subst_id
            asset_by_subst[asset.subst_id]["name"] = asset.subst_name
            asset_by_subst[asset.subst_id]["status"] = 100
            asset_by_subst[asset.subst_id]["assets"] = []
        asset_by_subst[asset.subst_id]["assets"].append(
            {
                "asset_type_name": asset.type_name,
                "status": asset_values.get(asset.guid, {}).get(status_code, "Undefined"),
            }
        )

    __calc_subst_status(asset_by_subst.values())
    result = {"substations": list(asset_by_subst.values())}
    return result, status


def get_subst_assets(subst_id: int, lang: str):
    """Получить данные об оборудовании подстанции."""
    tci_code = "hi_updated"
    status_code = "condition"
    sgn_last_codes = (tci_code, status_code)
    result = {}
    res_status = True
    try:
        substation = Substations.objects.get(id=subst_id)
    except Exception:
        return result, False
    else:
        result["id"] = substation.id
        result["name"] = substation.name
        result["scheme"] = substation.scheme_image.url if substation.scheme_image else ""
        result["assets"] = []

    assets = AssetsManager.get_by_subst(subst_id)
    if not assets:
        return result, res_status

    asset_last_values, query_status = __get_last_values_by_assets(assets, sgn_last_codes)
    res_status = res_status and query_status

    period_signals = SignalDesc.get_signals_from_codes((tci_code,))
    signals_by_source = SignalDesc.get_codes_by_source(period_signals, False)

    queries_params = []
    for asset in assets:
        timestamp_end = asset_last_values.get(asset.guid, {}).get(tci_code, {}).get("timestamp")
        if timestamp_end is None:
            continue
        timestamp_end = int(timestamp_end)
        timestamp_start = timestamp_end - 86400 * 30
        queries_params.append(
            {
                "asset_id": asset,
                "code_by_sources": signals_by_source,
                "date_start": timestamp_start,
                "date_end": timestamp_end,
                "is_reduced": True,
                "count_points": 30
            }
        )

    queries_results = []

    for query_params in queries_params:
        res = MeteringsManager.get_meterings(**query_params)
        queries_results.append(res[0])
        res_status = res_status and res[1]

    assets_info = {}
    for i, asset in enumerate(assets):
        last_values = asset_last_values.get(asset.guid, {})
        try:
            period_values = get_meterings_by_codes(queries_results[i])
        except Exception as ex:
            logger.error(f"Ошибка обработки данных за период для guid актива {asset.guid}. {ex}")
            period_values = {}
        assets_info[asset.guid] = {
            "asset_id": asset.id,
            "asset_type": asset.type_code,
            "name": asset.name,
            "status": get_status_name(
                last_values.get(status_code, {}).get("value")),
            "tci_last": Numeric.round_float(
                last_values.get(tci_code, {}).get("value"),
                ROUND_NDIGIT),
            "tci_period": period_values.get(tci_code, []),
            "on_scheme_x": asset.on_scheme_x,
            "on_scheme_y": asset.on_scheme_y
        }
    result["assets"] = sorted(
        assets_info.values(),
        key=lambda x: (x.get("asset_type", ""), x.get("name", "")))
    return result, res_status


def get_conclusion_table(lang: str):
    """Получить справочник диаг. заключений."""
    table_lines = deepcopy(CONCLUS_TABLE_LINES)
    ConclusTableLineTralslation.translate_collections(table_lines, lang)
    return {
        "notifications":
        [
            {
                "row": line._number,
                "notification": line._conclusion_name,
                "condition": line._requirement_name
            }
            for line in table_lines
        ]
    }


def get_company_struct():
    """Получить организационную структуру"""

    # get related `parent` field immediately in the same query
    substations = Substations.objects.select_related("parent").order_by("pk")
    return {
        "company_struct": [
            {
                "id": rec.pk,
                "name": rec.name,
                "parentId": rec.parent.pk if rec.parent else None,
                "sustId": rec.pk if rec.type == "end_node" else None,
                "typePoint": rec.type
            }
            for rec in substations
        ]
    }


def get_asset_type_tabs():
    """Получить вкладки графиков соответствующие типам активов"""
    result = {}
    for rec in (AssetsTypeChartTabs.objects.select_related("chart_tab", "asset_type")
                .all().only("chart_tab__code", "asset_type__code")):
        if rec.asset_type.code not in result:
            result[rec.asset_type.code] = []
        result[rec.asset_type.code].append(rec.chart_tab.code)
    return {
        "asset_type_tabs": [
            {
                "asset_type": type,
                "tabs": tabs
            }
            for type, tabs in result.items()
        ]
    }


def __calc_subst_status(substations: List[Dict[str, Union[str, int, float, list]]]):
    for subst in substations:
        asset_count = 0
        subst_state = 0
        for asset in subst["assets"]:
            asset_count += 1
            subst_state += txt_status_to_number100(asset.get("status", "Undefined"))
        subst_state = subst_state / asset_count
        subst["status"] = round(subst_state)


def __get_last_values_by_assets(assets: AssetDesc | List[AssetDesc], sgn_last_codes: Iterable[str]):
    """
    Возвращает последние значения сигналов в разрезе активов

    Return:
    ---
    - {asset_guid: {signal_code: {"value": str, "timestamp": float}, ...}, ...}
    """
    data, query_status = MeteringsManager.get_last_meterings(assets, sgn_last_codes)
    result = {}
    for record in data:
        if not isinstance(record, (list, tuple, ApgRec)) or len(record) < 4:
            continue
        asset_guid = record[0]
        if asset_guid not in result:
            result[asset_guid] = {}
        result[asset_guid][record[1]] = {
            "value": record[2],
            "timestamp": record[3]
        }
    return result, query_status
