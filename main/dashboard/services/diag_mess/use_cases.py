import logging
from datetime import datetime
from typing import Any, Dict, Iterable

from dashboard.services.commons.meterings_manager import MeteringsManager
from dashboard.services.commons.assets_manager import AssetsManager
from dashboard.services.commons.status import get_status_name
from dashboard.utils import time_func
from localization.services.translation.app_interface import APITralslation
from localization.services.translation.diag_msg import DiagMsgTralslation

from .formatters import to_subst_page
from .sql_msg_manager import SQLDiagMsgManager


logger = logging.getLogger(__name__)


def _get_qieried_fields(use_template: bool):
    """Получить список запрашиваемых полей из таблиц диаг. сообщений"""
    if use_template:
        return ("asset", "timestamp", "message_ids", "param_groups", "level", "id_tab", "signals")
    else:
        return ("asset", "timestamp", "message", "level", "id_tab", "signals")


def _get_message(msg_record: Dict[str, Any], translator: DiagMsgTralslation,
                 use_template: bool):
    """
    Получить текст диаг. сообщения. Если use_template = True, то предпринимается
    попытка получить текст из шаблонов и подстановочных аргументов, иначе
    берется значение из поля 'message'."""
    if use_template:
        return translator.get_translation(
            msg_record.get("message_ids"),
            msg_record.get("param_groups"))
    else:
        return msg_record.get("message", "")


def get_translation_latest(count: int = 5, lang: str = "ru", use_template: bool = True):
    """
    Получить последние диагностические сообщения
    по всей совокупности активов в количестве = count на заданном языке.
    Если use_template = True, то предпринимается
    попытка получить текст из шаблонов и подстановочных аргументов, иначе
    берется значение из поля 'message'.
    """
    result = {}
    if not isinstance(count, int):
        count = 5
    try:
        diag_msg = MeteringsManager.get_last_messages(
            asset_id=None,
            group="diag",
            count=count,
            fields=_get_qieried_fields(use_template))

        status = True
    except Exception:
        logger.exception(f"ERROR requesting a latest {count} diag messages")
        status = False
        diag_msg = []
    asset_guid = [record.get("asset") for record in diag_msg if record.get("asset")]
    assets = AssetsManager.dict_by_guid(AssetsManager.get_by_guids(asset_guid))
    if use_template:
        translator = DiagMsgTralslation.from_diag_msg(diag_msg, lang)
    else:
        translator = None
    result = {
        "diag_msg": [
            {
                "substation": get_property(assets, msg.get("asset"), "subst_name"),
                "asset_id": get_property(assets, msg.get("asset"), "id"),
                "asset_type": get_property(assets, msg.get("asset"), "type_code"),
                "asset": get_property(assets, msg.get("asset"), "name"),
                "msg": _get_message(msg, translator, use_template),
                "date": datetime.fromtimestamp(msg.get("timestamp")),
                "level": get_status_name(msg.get("level")),
                "id_tab": msg.get("id_tab"),
                "signals": msg.get("signals"),
            }
            for msg in diag_msg
            if msg.get("timestamp")]
    }
    return result, status


def get_last(asset_id: int = None, asset_guid: str = None,
             str_type: str = None, lang: str = "ru", use_template: bool = True):
    """
    Получить последнее диагностическое сообщение
    для актива.
    Если str_type != None, то ищется сообщение с заданным типом.
    Если use_template = True, то предпринимается
    попытка получить текст из шаблонов и подстановочных аргументов, иначе
    берется значение из поля 'message'.
    """
    if asset_id:
        asset_guid = AssetsManager.get_by_id(asset_id).guid
    result = {}
    try:
        diag_msg = MeteringsManager.get_last_messages(
            asset_id=asset_guid,
            group="diag",
            type_str=str_type,
            count=1,
            fields=_get_qieried_fields(use_template))

        if diag_msg:
            diag_msg = diag_msg[0]
        else:
            diag_msg = {}
        status = True
    except Exception:
        logger.exception("ERROR requesting a last diag message")
        status = False
        diag_msg = {}
    if use_template:
        translator = DiagMsgTralslation.from_diag_msg([diag_msg], lang)
    else:
        translator = None
    result = {
        "asset": asset_guid,
        "msg": _get_message(diag_msg, translator, use_template),
        "date": datetime.fromtimestamp(t) if (t := diag_msg.get("timestamp")) else "",
        "level": get_status_name(lvl) if (lvl := diag_msg.get("level")) else "",
    }
    return result, status


@time_func.runtime_in_log
def get_asset_diag_messages(obj_id: int, date_start: str, date_end: str,
                            is_subst: bool = True,
                            get_params: dict = None):
    """
    Получить диагностические сообщения для актива или подстанции.

    Parameters:
        ---
        - obj_id: int - идентификатор объекта, для которого выбираются сообщения;
        - is_subst: bool = True - если True, то сообщения выбираются
        для подстанции, если False, то для актива.
    """
    date_start, date_end = time_func.define_date_interval(
        date_start, date_end)
    count_diags, count_query_status = get_asset_count_diag_messages(
        obj_id, date_start, date_end, is_subst, get_params)
    if count_diags and isinstance(count_diags, Iterable):
        count_diags = count_diags[0]
        if count_diags and isinstance(count_diags, Iterable):
            count_diags = count_diags[0]
        else:
            count_diags = 0
    else:
        count_diags = 0

    filt_diags, messages_query_status = get_asset_raw_diag_messages(
        obj_id, date_start, date_end, is_subst, get_params)
    return (to_subst_page(filt_diags, count_diags),
            count_query_status and messages_query_status)


@time_func.runtime_in_log
def get_asset_count_diag_messages(
        obj_id: int,
        date_start: datetime, date_end: datetime,
        is_subst: bool = True,
        get_params: dict = None):
    """
    Получить кол-во диагностических сообщений для актива или подстанции.

    Parameters:
        ---
        - obj_id: int - идентификатор объекта, для которого выбираются сообщения;
        - is_subst: bool = True - если True, то сообщения выбираются
        для подстанции, если False, то для актива.
    """
    try:
        return SQLDiagMsgManager.count_per_interval(
            obj_id,
            date_start, date_end,
            is_subst,
            web_to_db_params(get_params)), True
    except Exception:
        if is_subst:
            what = "подстанции"
        else:
            what = "актива"
        logger.exception("Не удалось получить кол-во диагностических сообщений.\n"
                         f"ID {what}: {obj_id}\n"
                         f"Диапазон: [{date_start}, {date_end}]\n"
                         f"Аргументы для запроса: {get_params}")

        return [], False


@time_func.runtime_in_log
def get_asset_raw_diag_messages(
        obj_id: int,
        date_start: datetime, date_end: datetime,
        is_subst: bool = True,
        get_params: dict = None):
    """
    Получить диагностические сообщения для актива или подстанции.

    Parameters:
        ---
        - obj_id: int - идентификатор объекта, для которого выбираются сообщения;
        - is_subst: bool = True - если True, то сообщения выбираются
        для подстанции, если False, то для актива.
    """
    try:
        return SQLDiagMsgManager.per_interval(
            obj_id,
            date_start, date_end,
            is_subst,
            web_to_db_params(get_params)), True
    except Exception:
        if is_subst:
            what = "подстанции"
        else:
            what = "актива"
        logger.exception("Не удалось получить диагностические сообщения.\n"
                         f"ID {what}: {obj_id}\n"
                         f"Диапазон: [{date_start}, {date_end}]\n"
                         f"Аргументы для запроса: {get_params}")

        return [], False


def _get_localization_report_header(labels: list[str], defaults: list[str], lang: str):
    header_names = APITralslation.get_translts(labels, lang)
    for label, default in zip(labels, defaults):
        if header_names.get(label) is None:
            header_names[label] = default
    return header_names


@time_func.runtime_in_log
def get_subst_diag_messages_for_export(subst_id: int,
                                       date_start: str, date_end: str,
                                       get_params: dict = None,
                                       lang: str = None):
    """
    Получить диагностические сообщения для подстанции с id = subst_id
    для экспорта в файл
    """
    if not isinstance(get_params, dict):
        get_params = {}

    if lang is None:
        lang = "en"
    header_date_label = "d_mess_header_date"
    header_asset_label = "d_mess_header_asset"
    header_mess_label = "d_mess_header_mess"
    header_level_criticalily = "d_mess_header_criticalily"
    header_names = _get_localization_report_header(
        [header_date_label, header_asset_label, header_mess_label, header_level_criticalily],
        ["Date", "Asset", "Message", "Criticalily"],
        lang
    )

    date_start, date_end = time_func.define_date_interval(
        date_start, date_end)
    date_export = datetime.now(tz=time_func.get_tz())
    file_name = get_default_name_of_export_file(date_export, date_start, date_end)
    filt_diags, messages_query_status = get_asset_raw_diag_messages(
        subst_id, date_start, date_end, is_subst=True, get_params=get_params
    )
    result = {"headers": [header_names.get(header_date_label), header_names.get(header_asset_label),
                          header_names.get(header_mess_label), header_names.get(header_level_criticalily)]}
    result["data"] = [
        {
            header_names.get(header_date_label): str(timestamp),
            header_names.get(header_asset_label): asset_name,
            header_names.get(header_mess_label): message,
            header_names.get(header_level_criticalily): txt_level
        }
        for _, _, asset_name, timestamp, message, _, _, txt_level, _, _ in filt_diags
    ]
    return result, file_name, messages_query_status


def get_property(assets: Dict[str, Any], guid: str, property: str):
    """
    Возвращает из словаря активов для актива с требуемым guid
    значение требуемого property
    """
    return getattr(assets.get(guid), property, "")


def web_to_db_params(get_params: dict):
    """Возвращает словарь значений параметров для запроса объектов из БД"""
    keys = {
        "offset": "diagNumStart",
        "limit": "diagCount",
        "diag_type": "diagType",
        "search": "search",
        "order_field": "orderField",
        "order_type": "orderType",
        "lang": "lng",
        "use_template": "use_template",
    }
    return {output_key: get_params.get(input_key)
            for output_key, input_key in keys.items()}


def get_default_name_of_export_file(date_export: datetime,
                                    date_start: datetime, date_end: datetime):
    format = "%Y-%m-%d_%H-%M-%S"
    return (
        f"diag_messages__{datetime.strftime(date_export, format)}"
        f"__({datetime.strftime(date_start, format)}"
        f"--{datetime.strftime(date_end, format)})"
    )
