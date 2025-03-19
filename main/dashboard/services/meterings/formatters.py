import logging
from typing import List, Dict, Any, Union
from datetime import datetime
from json import loads
from itertools import zip_longest

from main.settings import ROUND_NDIGIT
from dashboard.utils import time_func
from dashboard.utils.number import Numeric
from dashboard.services.commons.signal_desc import SignalDesc
from dashboard.services.commons.status import get_status_name_without_undefined
from dashboard.services.commons.gd_table_line import GDTableLine
from config_ui.services.pasp_manager import PaspManager
from .added_signal import AddedSignal
from .overload_coeff import overload_coeffs
from .sgn_code_schemes import loadcapacity_table_code


logger = logger = logging.getLogger(__name__)


def _get_value_from_last(meterings_by_codes: Dict[str, Dict[str, Any]], code, default=None):
    return meterings_by_codes.get(code, {}).get("value", default)


def _get_timestamp_from_last(meterings_by_codes: Dict[str, Dict[str, Any]], code, default=None):
    return meterings_by_codes.get(code, {}).get("timestamp", default)


def _get_pdata_name(signal: SignalDesc):
    if signal._unit_name and signal._unit_name != "n/a":
        return f"{signal._name}, {signal._unit_name}"
    else:
        return signal._name


def _get_unit_for_chart(signal: SignalDesc):
    return (f"{signal._category_name if signal._category_name else 'Общие параметры'}"
            f"{', ' if signal._unit_name not in ('n/a', None) else ''}"
            f"{signal._unit_name if signal._unit_name not in ('n/a', None) else ''}")


def _get_name_with_unit(signal: SignalDesc, sep: str = ", "):
    return sep.join(
        (
            signal._name,
            f"{signal._unit_name if signal._unit_name not in ('n/a', None) else ''}"
        )
    )


def to_last_values_page(image: str,
                        signals: List[SignalDesc],
                        added_signals: List[AddedSignal],
                        pdata: List[SignalDesc],
                        dictionary_sgns: List[SignalDesc],
                        constants_sgns: List[SignalDesc],
                        meterings_by_codes: Dict[str, Any],
                        translts_phrases: Dict[str, str]):
    """
    Возвращает отформатированные данные для страницы
    последних значений сигналов.
    """
    last_vals_tables = {}
    for signal in signals:
        table_key = signal._last_val_table.code
        if table_key not in last_vals_tables:
            last_vals_tables[table_key] = {
                "title": signal._last_val_table.name,
                # код соответствующей вкладки графиков
                "sectionType": signal._last_val_table.chart_tab.code if signal._last_val_table.chart_tab else None,
                "parametrs": []
            }
        last_vals_tables[table_key]["parametrs"].append(
            {
                "code": signal._code,
                "title": signal._name,
                "measureUnit": f"({signal._unit_name})",
                "value": Numeric.round_float(_get_value_from_last(meterings_by_codes, signal._code), signal._precision),
                "state": get_status_name_without_undefined(_get_value_from_last(meterings_by_codes, signal._status_code))
            }
        )
    result = {
        "values_tables": list(last_vals_tables.values()),
        "image": image
    }
    for table in result["values_tables"]:
        table["parametrs"].sort(key=lambda x: x.get("code"))
    for signal in added_signals:
        result[signal.get_output_key()] = Numeric.round_float(
            signal.get_formatted_value(_get_value_from_last(meterings_by_codes, signal.get_code())),
            ROUND_NDIGIT)

    result["pData"] = []
    for title, signals in ([translts_phrases.get("asset_info_tbl_sect_pdatas", ""), pdata],
                           [translts_phrases.get("asset_info_tbl_sect_limits", ""), dictionary_sgns],
                           [translts_phrases.get("asset_info_tbl_sect_constants", ""), constants_sgns]):
        result["pData"].append(
            {
                "label": title,
                "value": "",
                "isBold": True
            })
        for signal in signals:
            if (value := _get_value_from_last(meterings_by_codes, signal._code)) is not None:
                result["pData"].append(
                    {
                        "label": _get_pdata_name(signal),
                        "value": value,
                        "isBold": False
                    })
    return result


@time_func.runtime_in_log
def get_additional_formatted_data_to_last_values_page(dictionary_sgns: List[SignalDesc],
                                                      constants_sgns: List[SignalDesc],
                                                      meterings_by_codes: Dict[str, Any]):
    pre_result = {}

    for sgns in (dictionary_sgns, constants_sgns):
        for sgn in sgns:
            value = meterings_by_codes.get(sgn._code)

            if value is not None:
                if sgn._category_id is not None:
                    cat_key = sgn._category_id
                else:
                    cat_key = 2000000000
                if cat_key not in pre_result:
                    pre_result[cat_key] = {
                        "title": sgn._category_name,
                        "values": {}
                    }
                sgn_key = sgn._code
                pre_result[cat_key]["values"][sgn_key] = {
                    "signal": sgn._name,
                    "unit": sgn._unit_name if sgn._unit_code not in {"na", ""} else None,
                    "value": value,
                }

    categories = []
    for key in sorted(pre_result.keys()):
        cat_data = pre_result.get(key, {})
        values = [
            cat_data.get("values", {}).get(key)
            for key in sorted(cat_data.get("values", {}).keys())
        ]
        cat_data["values"] = values
        categories.append(cat_data)

    return {"model_settings": {"categories": categories}}


@time_func.runtime_in_log
def get_passport_data_to_last_values_page(pasp_sgns: List[SignalDesc],
                                          pasp_manager: PaspManager,
                                          meterings_by_codes: Dict[str, Any],):
    """Возвращает паспорт актива для страницы состояния актива."""
    dict_pasp_sgns = {sgn._code: sgn for sgn in pasp_sgns}
    pre_result = {}
    p_sgn_settings = sorted(
        pasp_manager._p_signals.values(),
        key=lambda x: (x.category.order, x.order))

    for p_sgn in p_sgn_settings:
        sgn = dict_pasp_sgns.get(p_sgn.code)
        value = meterings_by_codes.get(p_sgn.code)
        if sgn and value is not None:
            cat_key = (p_sgn.category.order, p_sgn.category.code)
            if cat_key not in pre_result:
                pre_result[cat_key] = {
                    "title": p_sgn.category.name,
                    "values": []
                }
            pre_result[cat_key]["values"].append(
                {
                    "signal": sgn._name,
                    "unit": sgn._unit_name if sgn._unit_code not in {"na", ""} else None,
                    "value": value
                }
            )
    categories = [
        val
        for key in sorted(pre_result.keys())
        if (val := pre_result.get(key))
    ]
    return {"p_data": {"categories": categories}}


def to_charts_page(signals: List[SignalDesc],
                   forecast_sgns: List[SignalDesc],
                   data_for_period: list,
                   last_data: Dict[str, Any],
                   tab: str):
    """
    Возвращает отформатированные данные для страницы графиков.
    """
    result = {"params": []}
    meterings_by_codes = get_meterings_by_codes(data_for_period)
    tabs = [tab]
    signals.sort(key=lambda x: x._code.replace("_", "#"))
    for signal in signals:
        if sgn_meterings := meterings_by_codes.get(signal._code):
            signal_with_meterings = {
                "code": signal._code,
                "name": signal._name,
                "measure_unit": _get_unit_for_chart(signal),
                "tab": tabs,
                "mode": f"{'markers' if (signal._code.endswith('_offline') or signal._code.endswith('_off')) else 'lines'}",
                "visible": signal._visible,
                "dz": _get_value_from_last(last_data, signal._lim0_code, ""),
                "pdz": _get_value_from_last(last_data, signal._lim1_code, ""),
                "values": sgn_meterings
            }
            result["params"].append(signal_with_meterings)
    forecast_sgns.sort(key=lambda x: x._code.replace("_", "#"))
    for signal in forecast_sgns:
        if sgn_meterings := last_data.get(signal._code, {}).get("value"):
            try:
                sgn_meterings = loads(sgn_meterings)
            except Exception:
                logger.error(f"Не удалось десериализовать значение для сигнала {signal._code}")
                sgn_meterings = None
        if sgn_meterings:
            signal_with_meterings = {
                "code": signal._code,
                "name": signal._name,
                "measure_unit": _get_unit_for_chart(signal),
                "tab": tabs,
                "plot_type": 'forecast',
                "dz": "",
                "pdz": "",
                "values":  get_forecast_meterings(signal._code, sgn_meterings)
            }
            result["params"].append(signal_with_meterings)

    return result


def _get_v_lines_by_codes(
        meterings: list,
        selecting_codes: set,
        min_max_code_prefix: str):
    """
    Получить словарь соответствия кодов сигналов вертикальным линиям
    в моменты изменения значения сигнала
    """
    result = {code: [] for code in selecting_codes}
    prev_values = {code: None for code in selecting_codes}
    min_value = 0
    max_value = 0
    errors = {}

    for record in meterings:
        try:
            code: str = record[0]
            value = Numeric.round_float(record[2], ROUND_NDIGIT)
        except Exception as ex:
            if (err := str(ex)) not in errors:
                errors[err] = 1
            else:
                errors[err] = errors[err] + 1
            continue
        # определение min, max значений сигналов начинающихся с min_max_code_prefix
        if code.startswith(min_max_code_prefix):
            try:
                value = Numeric.form_float(record[2], ROUND_NDIGIT, 0)
            except Exception as ex:
                if (err := str(ex)) not in errors:
                    errors[err] = 1
                else:
                    errors[err] = errors[err] + 1
            else:
                min_value = min(min_value, value)
                max_value = max(max_value, value)
        # обработка значений сигналов из selecting_codes
        if code in selecting_codes:
            try:
                timestamp = datetime.fromtimestamp(record[1], time_func.get_tz()).replace(tzinfo=None)
            except Exception as ex:
                if (err := str(ex)) not in errors:
                    errors[err] = 1
                else:
                    errors[err] = errors[err] + 1
            else:
                # запись добавляется если текущее значение отличается от предыдущего
                if prev_values[code] != value:
                    prev_values[code] = value
                    result[code].append([timestamp])
    # удаляем из результата сигналы не имеющие отобранных записей
    for code in selecting_codes:
        if not result.get(code):
            result.pop(code)
    # добавляем min, max к каждой записи в результате
    if min_value == max_value:
        max_value += 2
    appended_values = (min_value, max_value)
    for code, data in result.items():
        for rec in data:
            rec.extend(appended_values)

    if errors:
        err_str = "".join((f"'{err}' в количестве {count} штук\n" for err, count in errors.items()))
        logger.error("При преобразовании значений полей измерений сигналов"
                     f" ({len(meterings)} строк)"
                     " возникли ошибки:\n"
                     f"{err_str}")
    return result


def to_overvoltage_table(last_data: Dict[str, Any], translts_phrases: Dict[str, str]):
    """
    Получить данные для отображения на вкладке графиков
    таблицы счетчиков перенапряжений.
    """

    table_11 = [
        [
            {"value": "1.1"}
        ],
        [
            {"value": translts_phrases.get("in_year", "")},
            {"value": translts_phrases.get("total", "")}
        ],
        [
            {
                "value": _get_value_from_last(last_data, "counter_overvoltage_excessive_duration_110_year"),
                "status": get_status_name_without_undefined(_get_value_from_last(last_data, "diag_counter_overvoltage_110_year"))

            },
            {"value": _get_value_from_last(last_data, "counter_overvoltage_excessive_duration_110_total")}
        ],
    ]
    table_125 = [
        [
            {"value": "1.25"}
        ],
        [
            {"value": translts_phrases.get("in_day", "")},
            {"value": translts_phrases.get("in_year", "")},
            {"value": translts_phrases.get("total", "")}
        ],
        [
            {
                "value": _get_value_from_last(last_data, "counter_overvoltage_excessive_duration_125_day"),
                "status": get_status_name_without_undefined(_get_value_from_last(last_data, "diag_counter_overvoltage_125_day"))
            },
            {
                "value": _get_value_from_last(last_data, "counter_overvoltage_excessive_duration_125_year"),
                "status": get_status_name_without_undefined(_get_value_from_last(last_data, "diag_counter_overvoltage_125_year"))
            },
            {
                "value": _get_value_from_last(last_data, "counter_overvoltage_excessive_duration_125_total"),
                "status": get_status_name_without_undefined(_get_value_from_last(last_data, "diag_counter_overvoltage_125_total"))
            }
        ],
    ]
    table_pause = [
        [
            {"value": translts_phrases.get("for_pause", "")}
        ],
        [
            {"value": translts_phrases.get("in_day", "")},
            {"value": translts_phrases.get("in_year", "")}
        ],
        [
            {"value": _get_value_from_last(last_data, "counter_overvoltage_excessive_pause_day")},
            {"value": _get_value_from_last(last_data, "counter_overvoltage_excessive_pause_year")},
        ],
    ]

    return {
        "table_11": table_11,
        "table_125": table_125,
        "table_pause": table_pause
    }


def to_overvoltage_charts(signals: List[SignalDesc],
                          data_for_period: List,
                          translts_phrases: Dict[str, str]):
    """
    Получить данные для отображения на графиках моментов перенапряжений
    в виде вертикальных линий
    """
    out_name = {
        "counter_overvoltage_excessive_duration_110_total": translts_phrases.get("overvolt_110_total_sgn_name", ""),
        "counter_overvoltage_excessive_duration_125_total": translts_phrases.get("overvolt_125_total_sgn_name", ""),
    }
    v_code_prefix = "u_p"

    v_lines_by_codes = _get_v_lines_by_codes(
        data_for_period,
        selecting_codes=set(out_name.keys()),
        min_max_code_prefix=v_code_prefix
    )
    v_lines = []
    for signal in signals:
        if sgn_v_lines := v_lines_by_codes.get(signal._code):
            signal_with_meterings = {
                "code": signal._code,
                "name": out_name.get(signal._code, signal._name),
                "measure_unit": f"{signal._category_name if signal._category_name else translts_phrases.get('cat_of_general_params_name', '')}",
                "values": sgn_v_lines
            }
            v_lines.append(signal_with_meterings)
    return {"v_lines": v_lines}


def _get_loadcapacity_message(last_data: Dict[str, Any], translts_phrases: Dict[str, str]):
    """
    Получить сообщение для вкладки графиков нагрузочной способности.
    """
    ndigit = 2
    result_message_parts = []
    message_1_parts = []
    if (table_num := _get_value_from_last(last_data, "table_overload_coeff_long_number")) == "8":
        result_message_parts.append(translts_phrases.get("loadcap_mess_for_tbl_coef_8", ""))
    elif table_num is not None:
        for code, template in (
                ("itsu_1044", translts_phrases.get("h_ind_insulation_phr", "")),
                ("itsu_1085", translts_phrases.get("h_ind_windings_phr", "")),
                ("its_1081_manual", translts_phrases.get("h_ind_magn_circ_phr", ""))):
            if (val := Numeric.round_float(_get_value_from_last(last_data, code), ndigit)) is not None:
                message_1_parts.append(template.format(val))
        if len(message_1_parts):
            result_message_parts.extend((translts_phrases.get("on_basis_phr", ""), ", ".join(message_1_parts)))
        table_num_template = translts_phrases.get("calculation_to_table_phr", "")
        if len(result_message_parts):
            result_message_parts.append(table_num_template.format(table_num))
        else:
            result_message_parts.append(table_num_template.capitalize().format(table_num))
    return " ".join(result_message_parts)


def _get_coeff_table(number: str, selected_cells: str, translts_phrases: Dict[str, str]):
    """
    Получить таблицу коэффициентов для вкладки графиков нагрузочной способности.
    """
    default_table_coeff = [["" for _ in range(8)] for _ in range(11)]

    if number not in ("2", "3", "4", "5", "6", "7"):
        selected_cells = []
    else:
        try:
            selected_cells = loads(selected_cells)
        except Exception:
            logger.error("Не удалось десериализовать список положений ячейки "
                         "в таблице коэффициентов допустимой перегрузки.")
            selected_cells = []
        selected_cells = set(tuple(cell) for cell in selected_cells)

    table = [
        [
            {"value": translts_phrases.get("duration_of_load_phr", "")},
            {"value": translts_phrases.get("table_overload_coeff_head", "")}
        ],
        [
            {"value": ""},
            {"value": -25}, {"value": -20}, {"value": -10}, {"value": -0},
            {"value": 10}, {"value": 20}, {"value": 30}, {"value": 40},
        ],
    ]
    durations = [f"20 {translts_phrases.get('secs', 'sec.')}",
                 f"1 {translts_phrases.get('min', 'min.')}",
                 f"5 {translts_phrases.get('mins_genitive', 'min.')}",
                 f"10 {translts_phrases.get('mins_genitive', 'min.')}",
                 f"20 {translts_phrases.get('mins_genitive', 'min.')}",
                 f"30 {translts_phrases.get('mins_genitive', 'min.')}",
                 f"1 {translts_phrases.get('hour', 'h.')}",
                 f"2 {translts_phrases.get('hour_genitive', 'h.')}",
                 f"4 {translts_phrases.get('hour_genitive', 'h.')}",
                 f"8 {translts_phrases.get('hours_genitive', 'h.')}",
                 f"24 {translts_phrases.get('hour_genitive', 'h.')}"]
    table_coeff = overload_coeffs.get(number, default_table_coeff)

    for y, line_coeff in enumerate(table_coeff):
        out_line_coeff = [{"value": durations[y]}]
        for x, val in enumerate(line_coeff):
            cell = {"value": val}
            if (y, x) in selected_cells:
                cell["selected"] = 1
            out_line_coeff.append(cell)
        table.append(out_line_coeff)

    return table


def to_loadcapacity_coeff(last_data: Dict[str, Any], translts_phrases: Dict[str, str]):
    """
    Возвращает сообщение и таблицу коэффициентов
    для вкладки графиков нагрузочной способности.
    """
    return {
        "message": _get_loadcapacity_message(last_data, translts_phrases),
        "coeff_table": _get_coeff_table(
            _get_value_from_last(last_data, "table_overload_coeff_long_number"),
            _get_value_from_last(last_data, "overload_coeff_num_in_table"),
            translts_phrases),
    }


def to_loadcapacity_table(signals_for_table: List[SignalDesc],
                          last_data: Dict[str, Any],
                          translts_phrases: Dict[str, str]):
    """
    Получить таблицу нагрузки для вкладки графиков нагрузочной способности.
    """
    def _get_sgn_name(signals_by_code: Dict[str, SignalDesc], code: str):
        sgn = signals_by_code.get(code)
        if isinstance(sgn, SignalDesc):
            return f"{sgn._name if sgn._name else sgn._code}"
        else:
            return code

    def _get_value(signals_by_code: Dict[str, SignalDesc], code: str, last_data: Dict[str, Any]):
        sgn = signals_by_code.get(code)
        if isinstance(sgn, SignalDesc):
            precison = sgn._precision
        else:
            precison = ROUND_NDIGIT

        value = Numeric.form_float(_get_value_from_last(last_data, code), precison)
        result = value
        if isinstance(sgn, SignalDesc) and value is not None:
            if sgn._unit_code == "s":
                time_parts = []
                if value == 0:
                    time_parts.append(f"0 {translts_phrases.get('sec_short', 'sec.')}")
                else:
                    for interval, unit in (
                            (86400, translts_phrases.get('day_short', 'd.')),
                            (3600, translts_phrases.get('hour_short', 'h.')),
                            (60, translts_phrases.get('min_short', 'min.')),
                            (1, translts_phrases.get('sec_short', 'sec.'))):
                        if num := int(value // interval):
                            time_parts.append(f"{num} {unit}")
                        value %= interval
                result = " ".join(time_parts)
            elif sgn._unit_name not in ('n/a', None):
                result = f"{value} {sgn._unit_name}"
        return result

    signals_by_code = {sgn._code: sgn for sgn in signals_for_table}
    table = [
        [
            {"value": _get_sgn_name(signals_by_code, code)},
            {"value": _get_value(signals_by_code, code, last_data)},
        ]
        for code in loadcapacity_table_code
    ]
    return {"load_table": table}


def get_meterings_by_codes(meterings: list):
    """Получить словарь соответствия кодов сигналов измерениям"""
    result = {}
    errors = {}
    local_tz = time_func.get_tz()
    for record in meterings:
        try:
            code = record[0]
            timestamp = datetime.fromtimestamp(record[1], local_tz).replace(tzinfo=None)
            value = Numeric.round_float(record[2], ROUND_NDIGIT)
        except Exception as ex:
            if (err := str(ex)) not in errors:
                errors[err] = 1
            else:
                errors[err] = errors[err] + 1
        else:
            if code not in result:
                result[code] = []
            result[code].append([timestamp, value])
    if errors:
        err_str = "".join((f"'{err}' в количестве {count} штук\n" for err, count in errors.items()))
        logger.error("При преобразовании значений полей измерений сигналов"
                     f" ({len(meterings)} строк)"
                     " возникли ошибки:\n"
                     f"{err_str}")
    return result


def get_forecast_meterings(code: str, meterings: list):
    """Получить отформатированный список прогнозных значений"""
    result = []
    errors = {}
    for record in meterings:
        try:
            timestamp = datetime.fromtimestamp(record[0], time_func.get_tz()).replace(tzinfo=None)
            value = Numeric.round_float(record[1], ROUND_NDIGIT)
        except Exception as ex:
            if (err := str(ex)) not in errors:
                errors[err] = 1
            else:
                errors[err] = errors[err] + 1
        else:
            result.append([timestamp, value])
    if errors:
        err_str = "".join((f"'{err}' в количестве {count} штук\n" for err, count in errors.items()))
        logger.error(f"При преобразовании значений полей прогноза сигнала {code}"
                     f" ({len(meterings)} строк)"
                     " возникли ошибки:\n"
                     f"{err_str}")
    return result


def get_meterings_by_timestamp(meterings: list):
    """Получить словарь соответствия штампов времени измерениям"""
    result = {}
    errors = {}
    for record in meterings:
        try:
            code = record[0]
            timestamp = record[1]
            value = Numeric.round_float(record[2], ROUND_NDIGIT)
        except Exception as ex:
            if (err := str(ex)) not in errors:
                errors[err] = 1
            else:
                errors[err] = errors[err] + 1
        else:
            if timestamp not in result:
                result[timestamp] = {}
            result[timestamp][code] = value
    if errors:
        err_str = "".join((f"'{err}' в количестве {count} штук\n" for err, count in errors.items()))
        logger.error("При преобразовании значений полей измерений сигналов"
                     f" в количестве {len(meterings)} строк"
                     " возникли ошибки:\n"
                     f"{err_str}")
    return result


def get_meterings_by_codes_synchronized_time(sgn_codes_to_out_key: dict, meterings: list):
    """
    Получить словарь соответствия сигналов спискам измерений
    синхронизированным по времени. В результате для каждого сигнала i-й элемент
    в списке измерений соответсвует i-му элементу в списке моментов времени.
    Если для какого-то момента времени отсутствует измерение хотя бы для
    одного сигнала, то этот момент времени не попадает в результат.
    В результате коды сигналов заменяются соотвествующим им выходным ключам
    из 'sgn_codes_to_out_key'.
    """
    result = {"dates": []}
    for out_key in sgn_codes_to_out_key.values():
        result[out_key] = []
    meterings_by_timestamp = get_meterings_by_timestamp(meterings)
    for timestamp, meterings in meterings_by_timestamp.items():
        try:
            date = datetime.fromtimestamp(timestamp, time_func.get_tz()).replace(tzinfo=None)
        except Exception:
            logger.exception(f"Ошибка преобразования {timestamp = } в дату.")
            continue
        data_in_timestamp = {}
        for code, out_key in sgn_codes_to_out_key.items():
            try:
                data_in_timestamp[out_key] = meterings[code]
            except Exception:
                logger.exception(f"Для даты {date} отсутствует значение для сигнала {code}.")
                continue
        result["dates"].append(date)
        for out_key, value in data_in_timestamp.items():
            result[out_key].append(value)
    return result


def to_duval_triangle(sgn_codes_to_out_key: dict, meterings: list):
    """Возвращает отформатированные данные для треугольника Дюваля"""
    return {
        "triangle": get_meterings_by_codes_synchronized_time(sgn_codes_to_out_key, meterings)
    }


def to_duval_pentagon(sgn_codes_to_out_key: dict, meterings: list):
    """Возвращает отформатированные данные для пятиугольника Дюваля"""
    return {
        "pentagon": get_meterings_by_codes_synchronized_time(sgn_codes_to_out_key, meterings)
    }


def to_rd_table(meterings_dict: dict, data_key: str, table_lines: GDTableLine):
    """
    Возвращает отформатированные данные по методике таблицы превышения лимитов
    отношений концентраций газов РД
    """
    volume_row = len(table_lines)
    try:
        data = loads(_get_value_from_last(meterings_dict, data_key))
    except Exception:
        data = [[None, None, None] for _ in range(volume_row)]
        logger.exception("Не удалось десериализовать значение для РД таблицы.")

    def _get_elem_by_index(data: Union[list, tuple], index: int):
        if not isinstance(data, (list, tuple)):
            logger.error(f"Не удалось получить элемент с индексом {index} из data, "
                         f"так как ожидается тип из('list', 'tuple'), получен {type(data)}.")
            return None
        if len(data) <= index:
            logger.error(f"Не удалось получить элемент с индексом {index} из data, "
                         f"{len(data) = }.")
            return None
        else:
            return data[index]

    return {
        "values": {
            info_line._number: {
                "defect": info_line._defect_name,
                "C2H2/C2H4": _get_elem_by_index(row, 0),
                "CH4/H2": _get_elem_by_index(row, 1),
                "C2H4/C2H6": _get_elem_by_index(row, 2),
                "exampels": info_line._example_name
            }
            for info_line, row in zip_longest(table_lines, data)
        }
    }


def to_rd_nomogram(meterings_dict: dict, model_status_key: str, data_key: str, diag_msg: str):
    """
    Возвращает отформатированные данные по методике номограмм РД
    """
    result = {"values": {}}
    if _get_value_from_last(meterings_dict, model_status_key) in ('0', None):
        return result
    else:
        try:
            data = loads(_get_value_from_last(meterings_dict, data_key))
        except Exception:
            logger.exception("Не удалось десериализовать значение для РД номограммы.")
            return result
        try:
            timestamp = _get_timestamp_from_last(meterings_dict, data_key)
            date = datetime.fromtimestamp(timestamp, time_func.get_tz())
        except Exception:
            logger.exception("Не удалось получить время результата диагностики для РД номограммы.")
            return result
        if data is None:
            logger.error("Значение диагностики по РД номограммам = None.")
            return result
        if not isinstance(data, dict):
            logger.error(f"Для значения диагностики по РД номограммам ожитается тип 'dict', получен '{type(data)}'")
            return result
        gases = ["h2", "ch4", "c2h6", "c2h4", "c2h2"]
        result["values"].update(
            {
                "data": date.replace(tzinfo=None),
                "gases": gases,
                "fact": [round(data.get("fact", {}).get(gas), ROUND_NDIGIT) for gas in gases],
                "etalon": [round(data.get("etalon", {}).get(gas), ROUND_NDIGIT) for gas in gases],
                "message": diag_msg
            }
        )
        return result


def to_forecast_3d(meterings_dict: dict, model_status_key: str, data_key: str, axe_templates: Dict[str, str]):
    """
    Возвращает отформатированные данные 3D прогноза.
    """
    result = {"params": []}
    if _get_value_from_last(meterings_dict, model_status_key) in ('0', None):
        return result
    else:
        try:
            data = loads(_get_value_from_last(meterings_dict, data_key))
        except Exception:
            logger.exception("Не удалось десериализовать значение для 3D прогноза.")
            return result

        if data is None:
            logger.error("Значение 3D прогноза = None.")
            return result
        if not isinstance(data, dict):
            logger.error(f"Для значения 3D прогноза ожидается тип 'dict', получен '{type(data)}'")
            return result
        codes = [{"in": "temperature", "out": "temp", "template": "forecast3DTempAxe"},
                 {"in": "i", "template": "forecast3DCurrentAxe"},
                 {"in": "h2", "out": "H2", "template": "forecast3DConcetrationAxe"},
                 {"in": "co", "out": "CO", "template": "forecast3DConcetrationAxe"},
                 {"in": "co2", "out": "CO2", "template": "forecast3DConcetrationAxe"},
                 {"in": "ch4", "out": "CH4", "template": "forecast3DConcetrationAxe"},
                 {"in": "c2h2", "out": "C2H2", "template": "forecast3DConcetrationAxe"},
                 {"in": "c2h4", "out": "C2H4", "template": "forecast3DConcetrationAxe"},
                 {"in": "c2h6", "out": "C2H6", "template": "forecast3DConcetrationAxe"}]
        for code in codes:
            result["params"].append(
                {
                    "code":  (out_code := code.get("out") if code.get("out") else code.get("in")),
                    "name": axe_templates.get(code.get("template"), "{}").format(out_code.upper()),
                    "values":  data.get(code.get("in"))
                }
            )
    return result


def to_hysteresis(signals: List[SignalDesc],
                  data_keys: list,
                  meterings: list):
    """
    Возвращает отформатированные данные для страницы графика гистерезиса.
    """
    result = {"params": []}
    if len(data_keys) < 2:
        return result
    signal_x = None
    signal_y = None
    for sgn in signals:
        if data_keys[0] == sgn._code:
            signal_x = sgn
        if data_keys[1] == sgn._code:
            signal_y = sgn
    if not signal_x and not signal_y:
        return result

    meterings_by_time = get_meterings_by_timestamp(meterings)
    data_x = []
    data_y = []
    for timestamp in sorted(meterings_by_time.keys()):
        x = meterings_by_time[timestamp].get(signal_x._code)
        y = meterings_by_time[timestamp].get(signal_y._code)
        if x is not None and y is not None:
            data_x.append(x)
            data_y.append(y)

    result["params"].append(
        {
            "name_x": _get_name_with_unit(signal_x),
            "name_y": _get_name_with_unit(signal_y),
            "x": data_x,
            "y": data_y
        }
    )

    return result
