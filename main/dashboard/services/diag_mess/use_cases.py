import logging
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict

from dashboard.services.commons.meterings_manager import MeteringsManager
from dashboard.services.commons.assets_manager import AssetsManager, AssetDesc
from dashboard.services.commons.status import get_status_name, diag_msg_status_eng_to_ru
from dashboard.utils import time_func
from localization.services.translation.app_interface import APITralslation
from localization.services.translation.diag_msg import DiagMsgTralslation

from .diag_config import QueryConfig, ProcessedConfig, PaginationConfig
from .input_params import InputParams
from .formatters import to_subst_page
from .vm_msg_manager import VMDiagMsgManager


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
        "date": datetime.fromtimestamp(t, time_func.get_tz()) if (t := diag_msg.get("timestamp")) else "",
        "level": get_status_name(lvl) if (lvl := diag_msg.get("level")) else "",
    }
    return result, status


@time_func.runtime_in_log
def get_asset_diag_messages(obj_id: int,
                            date_start: str, date_end: str,
                            get_params: dict = None):
    """
    Получить диагностические сообщения для актива.

    Parameters:
        ---
        - obj_id: int - идентификатор объекта, для которого выбираются сообщения;
    """
    input_params = InputParams.web_to_db_params(get_params)
    query_config = QueryConfig(**input_params)
    processed_config = ProcessedConfig(**input_params)
    try:
        filt_diags = get_messages_per_interval(
            obj_id=obj_id,
            date_start=date_start,
            date_end=date_end,
            query_config=query_config,
            processed_config=processed_config)
        diags_query_status = True
    except Exception as ex:
        logger.error(
            "Не удалось получить диаг сообщения для: "
            f"{obj_id = }, {date_start = }, {date_end = }. {ex}")
        filt_diags = []
        diags_query_status = False
    pagin_config = PaginationConfig(**input_params)
    count_diags = len(filt_diags)
    filt_diags = filt_diags[pagin_config.get_start_slice():pagin_config.get_end_slice()]
    return to_subst_page(filt_diags, count_diags), diags_query_status


@time_func.runtime_in_log
@lru_cache(maxsize=10)
def get_messages_per_interval(
        obj_id: int,
        date_start: str,
        date_end: str,
        query_config: QueryConfig,
        processed_config: ProcessedConfig):
    """
    Получить обработанные диаг сообщения за требуемый период
    с учетом параметров конфигурации запроса и обработки.
    При ошибке запроса генерирует исключение!
    """
    date_start, date_end = time_func.define_date_interval(
        date_start, date_end)
    asset = AssetsManager.get_by_id(obj_id)
    if asset.guid:
        raw_diags, diags_query_status = VMDiagMsgManager.per_interval(
            asset.guid, date_start, date_end, query_config)
        if not diags_query_status:
            raise ValueError("Ошибка при запросе из БД диаг. сообщений.")
    else:
        raw_diags = []
        raise ValueError(f"У актива с id = {asset.id} отсутствует GUID.")

    filt_diags = _get_processed_messages(raw_diags, processed_config, asset)
    _sorting_messages(filt_diags, processed_config)
    return filt_diags


@time_func.runtime_in_log
def _get_processed_messages(raw_diags: list[dict], config: ProcessedConfig, asset: AssetDesc):
    """
    Получить обработанные диаг. сообщения из списка сырых (из запроса)
    записей диаг. сообщений.
    """
    if raw_diags:
        translator = DiagMsgTralslation([], config._lang)
        filt_diags = [
            processed_rec
            for rec in raw_diags
            if (processed_rec := _get_processed_msg_record(
                rec, translator, asset, config._search))]
    else:
        filt_diags = []
    return filt_diags


def _get_processed_msg_record(
            rec: dict,
            translator: DiagMsgTralslation,
            asset: AssetDesc,
            search: str):
    """Получить обработанную запись диаг. сообщения"""
    msg_time = time_func.normalize_date(rec["_time"])
    if not msg_time:
        return None
    str_msg_time = msg_time.strftime("%Y-%m-%d %H:%M:%S")

    raw_msg = rec.get("_msg", "").strip()
    loc_msg = translator.get_translation(
        rec.get("message_ids"),
        rec.get("param_groups"))
    if not (msg := loc_msg or raw_msg):
        return None

    exclude_messages = set(("null", "[]", "{}", "()"))
    if msg.strip() in exclude_messages:
        return None

    asset_name = asset.name or ""

    search = search.lower()
    result_search = (
        msg.lower().find(search) > -1 or asset_name.lower().find(search) > -1
        or str_msg_time.lower().find(search) > -1)
    if not result_search:
        return None

    return {
        "time": str_msg_time,
        "message": msg,
        "asset_name": asset_name,
        "asset": asset.id,
        "asset_type": asset.type_code,
        "level": get_status_name(rec.get("level")),
        "level_txt": diag_msg_status_eng_to_ru(get_status_name(rec.get("level"))),
        "group": rec.get("group"),
        "_time": rec.get("_time"),
        "id_tab": rec.get("id_tab"),
        "signals": rec.get("signals"),
    }


@time_func.runtime_in_log
def _sorting_messages(diags: list[dict], config: ProcessedConfig):
    """Отсортировать записи диаг. сообщений"""
    diags.sort(
        key=lambda x: x.get(config.get_order_field()),
        reverse=config.is_order_reverse())


def _get_localization_report_header(labels: list[str], defaults: list[str], lang: str):
    header_names = APITralslation.get_translts(labels, lang)
    for label, default in zip(labels, defaults):
        if header_names.get(label) is None:
            header_names[label] = default
    return header_names


@time_func.runtime_in_log
def get_asset_diag_messages_for_export(obj_id: int,
                                       date_start: str, date_end: str,
                                       get_params: dict = None,
                                       lang: str = None):
    """
    Получить диагностические сообщения для подстанции с id = subst_id
    для экспорта в файл
    """
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
    datetime_start, datetime_end = time_func.define_date_interval(
        date_start, date_end)
    date_export = datetime.now(tz=time_func.get_tz())
    file_name = get_default_name_of_export_file(date_export, datetime_start, datetime_end)

    result = {"headers": [header_names.get(header_date_label), header_names.get(header_asset_label),
                          header_names.get(header_mess_label), header_names.get(header_level_criticalily)]}

    input_params = InputParams.web_to_db_params(get_params)
    query_config = QueryConfig(**input_params)
    processed_config = ProcessedConfig(**input_params)
    try:
        filt_diags = get_messages_per_interval(
            obj_id=obj_id,
            date_start=date_start,
            date_end=date_end,
            query_config=query_config,
            processed_config=processed_config)
        diags_query_status = True
    except Exception as ex:
        logger.error(
            "Не удалось получить диаг сообщения для: "
            f"{obj_id = }, {date_start = }, {date_end = }. {ex}")
        filt_diags = []
        diags_query_status = False

    result["data"] = [
        {
            header_names.get(header_date_label): rec.get("time"),
            header_names.get(header_asset_label): rec.get("asset_name"),
            header_names.get(header_mess_label): rec.get("message"),
            header_names.get(header_level_criticalily): rec.get("level_txt")
        }
        for rec in filt_diags
    ]
    return result, file_name, diags_query_status


def get_property(assets: Dict[str, Any], guid: str, property: str):
    """
    Возвращает из словаря активов для актива с требуемым guid
    значение требуемого property
    """
    return getattr(assets.get(guid), property, "")


def get_default_name_of_export_file(date_export: datetime,
                                    date_start: datetime, date_end: datetime):
    format = "%Y-%m-%d_%H-%M-%S"
    return (
        f"diag_messages__{datetime.strftime(date_export, format)}"
        f"__({datetime.strftime(date_start, format)}"
        f"--{datetime.strftime(date_end, format)})"
    )
