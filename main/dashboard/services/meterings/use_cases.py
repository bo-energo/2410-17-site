import asyncio
import logging
from copy import deepcopy
from json import loads

from dashboard.utils import time_func
from dashboard.services.commons.signal_desc import SignalDesc
from dashboard.services.commons.assets_manager import AssetsManager
from dashboard.services.commons.meterings_manager import MeteringsManager, AssetDesc
from dashboard.services.commons.gd_table_line import GD_TABLE_LINES
from dashboard.services.diag_mess.use_cases import get_last
from .added_signal import AddedSignal
from . import formatters
from . import sgn_code_schemes
from . import api_label_schemes
from localization.services.translation.signal import SignalDescTralslation
from localization.services.translation.pasp_signal import PaspSignalTralslation
from localization.services.translation.gd_table import GDTableLineTralslation
from localization.services.translation.app_interface import APITralslation
from config_ui.services.block_manager import BlockManager
from config_ui.services.pasp_manager import PaspManager


logger = logging.getLogger(__name__)

ASSET_MODEL_LABEL = "assetType"


@time_func.runtime_in_log
def _get_added_passport_signals(signals_settings: dict[dict]):
    """Возвращает список дополнительных паспортных сигналов."""
    result: list[SignalDesc] = []
    for code, value in signals_settings.items():
        name = value.get("name")
        if name:
            result.append(
                SignalDesc(
                    id=None,
                    code=code,
                    name=name,
                    unit_code=value.get("unit_code"),
                    unit_name=value.get("unit_name"),
                    storage=None,
                    ))
    return result


def get_asset_desc(func: object):
    """
    Заменяет в принимаемых аргументах 'id актива' на соответсвующий актив.
    'id актива' должен быть первым неименованным аргументом.
    """
    def wrapper(*args, **kwargs):
        try:
            asset_id = args[0]
        except Exception:
            logger.error(f"Для {func.__module__}.{func.__qualname__} ожидается "
                         f"как минимум один аргумент - id актива (int)")
            return {}, False
        asset = AssetsManager.get_by_id(asset_id)
        if asset is None:
            logger.error(f"Для {func.__module__}.{func.__qualname__} "
                         f"не удалось получить актив с id = {asset_id}")
            return {}, False
        return func(asset, *args[1:], **kwargs)
    return wrapper


def _get_added_pdata_signaldesc(lang: str):
    asset_model_code = "asset_model"
    asset_model_label = ASSET_MODEL_LABEL
    asset_model_name = APITralslation.get_translts([asset_model_label], lang)
    return SignalDesc(None,
                      asset_model_code,
                      asset_model_name.get(asset_model_label),
                      None, None, None)


@get_asset_desc
def get_last_meterings_v2(asset: AssetDesc, lang: str):
    """Получить последние значения сигналов для актива с asset_id"""
    asset_model_label = ASSET_MODEL_LABEL
    asset_model_code = "asset_model"

    block_manager = BlockManager(asset.id, "last_val")
    pasp_manager = PaspManager()
    last_signals, pasp_sgns, period_signals = SignalDesc.get_signals_from_codes(
        (
            block_manager.last_data_links.get_codes(),
            pasp_manager.get_signals_codes(),
            block_manager.period_data_links.get_codes(),

        )
    )

    if asset.type_code == "transformer":
        added_signals = AddedSignal.from_args_list(
            [["life_loss_day", "aging_per_day", lambda x: round(24 * float(x), 2)],
             ["hi_updated", "tci_last", lambda x: round(float(x), 2)]]
        )
    else:
        added_signals = []

    dictionary_sgns = sorted(SignalDesc.get_signals_for_type("dictionaries"), key=lambda x: x._code)
    constants_sgns = sorted(SignalDesc.get_signals_for_type("constants"), key=lambda x: x._code)

    SignalDescTralslation.translate_collections(
        [dictionary_sgns, constants_sgns, pasp_sgns], lang)
    SignalDescTralslation.translate_collections(
        [last_signals, period_signals], lang, {"sg_name"})
    PaspSignalTralslation.translate_collections(
       pasp_manager.get_signals(), lang)
    pasp_manager._p_category
    units = SignalDescTralslation.get_unit_translations(block_manager.units.get_codes(), lang)
    back_labels_codes = block_manager.back_labels.get_codes()
    back_labels_codes.update(
        (
            "asset_info_tbl_sect_pdatas", "asset_info_tbl_sect_limits",
            "asset_info_tbl_sect_constants", asset_model_label)
    )
    back_labels = APITralslation.get_translts(list(back_labels_codes), lang)

    last_signals_codes = SignalDesc.get_codes(
        (last_signals, period_signals, dictionary_sgns, constants_sgns, pasp_sgns),
        False)
    last_signals_codes.update(AddedSignal.get_codes(added_signals))
    last_data, last_data_status = MeteringsManager.get_last_meterings(
        asset,
        last_signals_codes)

    last_timestamp_by_codes = MeteringsManager.get_last_meterings_timestamp_by_codes(
        last_data)
    block_manager.period_data_links.set_last_date(last_timestamp_by_codes)

    last_data = MeteringsManager.get_last_meterings_by_codes(last_data, True)

    added_p_sgn_configs = {
        asset_model_code: {
            "order": 0,
            "category": "pdata_main",
            "name": back_labels.get(asset_model_label)}}
    pasp_manager.add_psignals_from_dict(added_p_sgn_configs)
    added_pasp_sgns = _get_added_passport_signals(added_p_sgn_configs)
    if isinstance(pasp_sgns, list):
        pasp_sgns.extend(added_pasp_sgns)
    last_data[asset_model_code] = asset.model

    for signal in added_signals:
        last_data[signal.get_code()] = signal.get_formatted_value(last_data.get(signal.get_code()))

    period_data, period_data_status = __get_period_data_for_widgets(
        block_manager, period_signals, asset)

    signals_precision = {}
    for signals in (last_signals, period_signals):
        for sgn in signals:
            signals_precision[sgn._code] = sgn._precision
    result = {
        "object_id": asset.subst_id,
        "object_name": asset.subst_name,
        "asset_name": asset.name,
        "asset_type": asset.type_code
    }
    result.update(
        {sgn.get_output_key(): last_data.get(signal.get_code()) for sgn in added_signals})
    result.update(
        block_manager.get_data_to_page(
            signals_precision,
            last_data,
            period_data,
            {"image_url": asset.get_image_url(), "scheme_image_url": asset.get_scheme_image_url()},
            units,
            back_labels)
    )
    result.update(
        formatters.get_additional_formatted_data_to_last_values_page(
            dictionary_sgns, constants_sgns, last_data)
    )
    result.update(
        formatters.get_passport_data_to_last_values_page(
            pasp_sgns, pasp_manager, last_data)
    )
    return result, period_data_status or last_data_status


def _loads_signals(signals: str | None):
    """Получить список кодов сигналов десериализованный из входной строки"""
    try:
        signals = loads(signals)
    except Exception as ex:
        logger.error(f"Не удалось получить список сигналов из '{signals}'. {ex}")
        signals = list()
    if not isinstance(signals, (list, tuple)):
        logger.error(f"Сигналы для графика ожидаются типа list | tuple, получен {type(signals)}")
        signals = list()
    return signals


@get_asset_desc
def get_meterings_for_charts(asset: AssetDesc,
                             date_start: str | None, date_end: str | None,
                             tab: str, input_sgn_codes: str | None, lang: str):
    """Получить значения сигналов для актива с asset_id за временной диапазон"""
    overvoltage_tab = "overvoltage"
    loadcapacity_tab = "loadcapacity"
    t_now = time_func.now_with_tz(None)
    date_start, date_end = time_func.define_date_interval(date_start, date_end)
    input_sgn_codes = _loads_signals(input_sgn_codes)
    (
        signals,
        offline_signals,
        limits,
        forecast_sgns) = SignalDesc.get_signals_for_charts_with_diag_message_signals(
            asset.id, tab, input_sgn_codes)
    if t_now.date() != date_end.date():
        forecast_sgns = []

    signals_for_table = []
    signals_for_v_line = []
    signals_for_loadcap_table = []
    if tab == overvoltage_tab:
        signals_for_table, signals_for_v_line = SignalDesc.get_signals_from_codes(
            (sgn_code_schemes.overvoltage_table_code,
             sgn_code_schemes.overvoltage_v_line_code))
    elif tab == loadcapacity_tab:
        signals_for_loadcap_table = SignalDesc.get_signals_from_codes(
             sgn_code_schemes.loadcapacity_table_code)

    SignalDescTralslation.translate_collections(
        [signals, offline_signals, forecast_sgns, signals_for_v_line, signals_for_loadcap_table],
        lang)

    signals_by_source = SignalDesc.get_codes_by_source(
        signals + signals_for_v_line, False)
    offline_signals_by_source = SignalDesc.get_codes_by_source(offline_signals, False)
    last_signals_codes = SignalDesc.get_codes(
        (limits, forecast_sgns, signals_for_table, signals_for_loadcap_table),
        False)
    if tab == loadcapacity_tab:
        last_signals_codes.update(
            ("overload_coeff_num_in_table", "itsu_1044", "itsu_1085",
             "table_overload_coeff_long_number", "its_1081_manual")
        )

    task_query_last_data = MeteringsManager.get_last_meterings_by_codes_sync(asset, last_signals_codes)
    task_query_period_data = MeteringsManager.get_meterings(
        asset,
        signals_by_source,
        date_start.timestamp(), date_end.timestamp(),
        True
    )

    task_query_off_period_data = MeteringsManager.get_meterings(
        asset,
        offline_signals_by_source,
        date_start.timestamp(), date_end.timestamp(),
        False
    )

    res_query_period_data = task_query_period_data
    res_query_off_period_data = task_query_off_period_data
    res_query_last_data = task_query_last_data
    res_query_period_data[0].extend(res_query_off_period_data[0])
    res_query_period_data = (
        res_query_period_data[0],
        res_query_period_data[1] or res_query_off_period_data[1]
    )
    result_query_period_data, result_query_last_data = res_query_period_data, res_query_last_data

    data_for_period, data_for_period_status = result_query_period_data
    last_data, last_data_status = result_query_last_data

    signals.extend(offline_signals)
    result = formatters.to_charts_page(signals, forecast_sgns, data_for_period, last_data, tab)
    if tab == overvoltage_tab:
        translts_phrases = APITralslation.get_translts(
            api_label_schemes.overvolt_tab, lang)
        result.update(formatters.to_overvoltage_table(last_data, translts_phrases))
        result.update(formatters.to_overvoltage_charts(
            signals_for_v_line, data_for_period, translts_phrases))
    elif tab == loadcapacity_tab:
        translts_phrases = APITralslation.get_translts(
            api_label_schemes.loadcap_tab, lang)
        result.update(formatters.to_loadcapacity_coeff(last_data, translts_phrases))
        result.update(formatters.to_loadcapacity_table(signals_for_loadcap_table, last_data, translts_phrases))
    return result, data_for_period_status or last_data_status


@get_asset_desc
def get_rd_table(asset: AssetDesc, lang: str):
    """Получить статусы превышения лимитов отношений газов по методике РД"""
    data_key = "diag_c_model1rd_tbl"
    last_data, status = MeteringsManager.get_last_meterings(
        asset,
        (data_key,))
    meterings_dict = MeteringsManager.get_last_meterings_by_codes(last_data)

    table_lines = deepcopy(GD_TABLE_LINES)
    GDTableLineTralslation.translate_collections(table_lines, lang)

    return formatters.to_rd_table(meterings_dict, data_key, table_lines), status


@get_asset_desc
def get_duval_triangle(asset: AssetDesc, date_start: str | None, date_end: str | None):
    """Получить отношения концентраций газов по методу треугольника Дюваля"""
    sgn_codes_to_out_key = {
        "diag_c_duval31_r_c2h4": "C2H4", "diag_c_duval31_r_c2h2": "C2H2",
        "diag_c_duval31_r_ch4": "CH4"}
    signals = SignalDesc.get_signals_from_codes(sgn_codes_to_out_key.keys())
    date_start, date_end = time_func.define_date_interval(date_start, date_end)
    meterings, status = MeteringsManager.get_meterings(
        asset,
        SignalDesc.get_codes_by_source(signals, False),
        date_start.timestamp(), date_end.timestamp())
    return formatters.to_duval_triangle(sgn_codes_to_out_key, meterings), status


@get_asset_desc
def get_duval_pentagon(asset: AssetDesc, date_start: str | None, date_end: str | None):
    """
    Получить координаты точки статуса концентраций газов
    для пятиугольника Дюваля
    """
    sgn_codes_to_out_key = {
        "diag_c_duval51_c_x": "x", "diag_c_duval51_c_y": "y",
        "diag_c_duval51_c_h2": "h2", "diag_c_duval51_c_ch4": "ch4",
        "diag_c_duval51_c_c2h4": "c2h4", "diag_c_duval51_c_c2h6": "c2h6",
        "diag_c_duval51_c_c2h2": "c2h2"}
    signals = SignalDesc.get_signals_from_codes(sgn_codes_to_out_key.keys())
    date_start, date_end = time_func.define_date_interval(date_start, date_end)
    meterings, status = MeteringsManager.get_meterings(
        asset,
        SignalDesc.get_codes_by_source(signals, False),
        date_start.timestamp(), date_end.timestamp())
    return formatters.to_duval_pentagon(sgn_codes_to_out_key, meterings), status


@get_asset_desc
def get_rd_nomogram(asset: AssetDesc, lang: str, use_template: bool):
    """Получить данные диагностики по методу номограмм"""
    model_status_key = "diag_c_model2rd"
    data_key = "diag_c_model2rd_nomogram"
    msg_type = "diag_nomogram_rd"
    last_data, status1 = MeteringsManager.get_last_meterings(
        asset,
        (model_status_key,  data_key))
    meterings_dict = MeteringsManager.get_last_meterings_by_codes(last_data)
    diag_msg, status2 = get_last(asset_guid=asset.guid, str_type=msg_type, lang=lang,
                                 use_template=use_template)
    return formatters.to_rd_nomogram(meterings_dict, model_status_key, data_key,
                                     diag_msg.get("msg", "")), status1 and status2


@get_asset_desc
def get_forecast_3d(asset: AssetDesc, lang: str):
    """Получить данные диагностики по методу номограмм"""
    model_status_key = "diag_c_forecast_3d"
    data_key = "c_forecast_3d"

    last_data, status = MeteringsManager.get_last_meterings(
        asset,
        (model_status_key,  data_key))
    meterings_dict = MeteringsManager.get_last_meterings_by_codes(last_data)
    axe_templates = APITralslation.get_translts(["forecast3DTempAxe", "forecast3DCurrentAxe", "forecast3DConcetrationAxe"], lang)
    return formatters.to_forecast_3d(meterings_dict, model_status_key, data_key, axe_templates), status


@get_asset_desc
def get_hysteresis(asset: AssetDesc,
                   date_start: str | None, date_end: str | None,
                   tab: str, lang: str):
    """Получить гистерезис сигналов для актива с asset_id за временной диапазон"""
    signals_codes_by_tabs = {
        "humidity": ["t_bt", "rs"]
    }
    data_keys = signals_codes_by_tabs.get(tab, [])
    signals = SignalDesc.get_signals_from_codes(data_keys)
    SignalDescTralslation.translate_collections([signals], lang)

    date_start, date_end = time_func.define_date_interval(date_start, date_end)

    meterings, meter_status = MeteringsManager.get_meterings(
        asset,
        SignalDesc.get_codes_by_source(signals, False),
        date_start.timestamp(), date_end.timestamp())
    return (formatters.to_hysteresis(signals, data_keys, meterings),
            meter_status)


@get_asset_desc
def get_passport_data(asset: AssetDesc, lang: str):
    """Получить данные паспорта для актива с asset_id"""
    title_label = "asset_info_tbl_sect_pdatas"
    object_name_label = "object_name"
    asset_label = "d_mess_header_asset"
    asset_model_label = ASSET_MODEL_LABEL

    pasp_manager = PaspManager()
    pasp_sgns = SignalDesc.get_signals_from_codes(pasp_manager.get_signals_codes())

    SignalDescTralslation.translate_collections([pasp_sgns], lang)
    PaspSignalTralslation.translate_collections(
       pasp_manager.get_signals(), lang)

    last_signals_codes = SignalDesc.get_codes((pasp_sgns), False)
    last_data, last_data_status = MeteringsManager.get_last_meterings(
        asset,
        last_signals_codes)
    last_data = MeteringsManager.get_last_meterings_by_codes(last_data, True)

    back_labels = APITralslation.get_translts(
        [title_label, object_name_label, asset_label, asset_model_label], lang)

    result = {
        "title": back_labels.get(title_label),
        "title_page": [
            {"name": back_labels.get(object_name_label), "value": asset.subst_name},
            {"name": back_labels.get(asset_label), "value": asset.name},
            {"name": back_labels.get(asset_model_label), "value": asset.model},
        ]
    }
    result.update(
        formatters.get_passport_data_to_last_values_page(
            pasp_sgns, pasp_manager, last_data).get("p_data", {})
    )
    return result, last_data_status


@get_asset_desc
def get_diag_sett_data(asset: AssetDesc, lang: str):
    """Получить данные настройки диагностики для актива с asset_id"""
    title_label = ["asset_info_tbl_sect_limits", "asset_info_tbl_sect_constants"]
    object_name_label = "object_name"
    asset_label = "d_mess_header_asset"
    asset_model_label = ASSET_MODEL_LABEL

    dictionary_sgns = sorted(SignalDesc.get_signals_for_type("dictionaries"), key=lambda x: x._code)
    constants_sgns = sorted(SignalDesc.get_signals_for_type("constants"), key=lambda x: x._code)

    SignalDescTralslation.translate_collections(
        [dictionary_sgns, constants_sgns], lang)

    last_signals_codes = SignalDesc.get_codes((dictionary_sgns, constants_sgns), False)
    last_data, last_data_status = MeteringsManager.get_last_meterings(
        asset,
        last_signals_codes)
    last_data = MeteringsManager.get_last_meterings_by_codes(last_data, True)

    back_labels = APITralslation.get_translts(
        [*title_label, object_name_label, asset_label, asset_model_label], lang)

    result = {
        "title": ", ".join(back_labels.get(label) for label in title_label),
        "title_page": [
            {"name": back_labels.get(object_name_label), "value": asset.subst_name},
            {"name": back_labels.get(asset_label), "value": asset.name},
            {"name": back_labels.get(asset_model_label), "value": asset.model},
        ]
    }
    result.update(
        formatters.get_additional_formatted_data_to_last_values_page(
            dictionary_sgns, constants_sgns, last_data).get("model_settings", {})
    )
    return result, last_data_status


@time_func.runtime_in_log
def __get_period_data_for_widgets(
        block_manager: BlockManager, period_signals: list[SignalDesc], asset: AssetDesc):
    period_data = dict()
    period_data_status = True
    period_signals_by_codes = {sgn._code: sgn for sgn in period_signals}
    for link in block_manager.period_data_links.links:
        if (sgn := period_signals_by_codes.get(link.code)):
            sgn_data, query_status = MeteringsManager.get_meterings(
                asset,
                {sgn._storage: set((sgn._code, ))},
                link.last_date - link.period, link.last_date,
                )
            sgn_data = formatters.get_meterings_by_codes(sgn_data)
            for code, data in sgn_data.items():
                if code not in period_data:
                    period_data[code] = dict()
                period_data[code][link.period] = data
            period_data_status = period_data_status or query_status
    return period_data, period_data_status
