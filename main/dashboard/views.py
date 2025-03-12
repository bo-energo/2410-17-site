import logging
import json
from itertools import groupby

from django.http import JsonResponse
from django.shortcuts import render

from dashboard.services.diag_mess import use_cases as diagmsg_use_cases
from dashboard.services.export import use_cases as export_use_cases
from dashboard.services.geomap import use_cases as geomap_use_cases
from dashboard.services.meterings import use_cases as meter_use_cases
from dashboard.services.signal_stats import use_cases as stats_use_cases
from dashboard.services.substation import use_cases as subst_use_cases
from dashboard.utils import request_status, time_func
from dashboard.utils.time_func import DATE_FORMAT_STR, datestr_to_timestamp, timestamp_to_server_datestr


logger = logging.getLogger(__name__)

USE_DIAG_TEMPLATE = True


def index(request):
    return render(request, 'index.html')


@time_func.runtime_in_log
def substations(request) -> object:
    """
    Возвращает список подстанций с типами входящего в них оборудования.
    Для подстанций и оборудования указывается их статус.
    """
    req_status = request_status.RequestStatus(True)
    get = request.GET
    result, status = subst_use_cases.get_all_assets_with_statuses(lang=get.get("lng"))
    req_status.add(status, "Ошибка формирования списка оборудования")
    result["status"] = req_status.get_message()

    return JsonResponse(
            result,
            json_dumps_params={'ensure_ascii': False},
            status=req_status.get_number_status()
    )


@time_func.runtime_in_log
def substation_info(request, objId: int) -> object:
    """Возвращает информацию о подстанции"""
    req_status = request_status.RequestStatus(True)
    get = request.GET
    result, status = subst_use_cases.get_subst_assets(objId, lang=get.get("lng"))
    req_status.add(status, "Ошибка формирования списка оборудования")
    result["status"] = req_status.get_message()
    return JsonResponse(
            result,
            json_dumps_params={'ensure_ascii': False},
            status=req_status.get_number_status()
    )


@time_func.runtime_in_log
def asset_diag_mess(request, objId: int, is_subst: bool = True) -> object:
    """Возвращает диагностические сообщения для актива или подстанции"""
    req_status = request_status.RequestStatus(True)
    get = request.GET
    if not isinstance(get, dict):
        get = {}
    else:
        get = dict(get.items())
    get["use_template"] = USE_DIAG_TEMPLATE
    result, status = diagmsg_use_cases.get_asset_diag_messages(
        obj_id=objId,
        date_start=get.get("dateStart"),
        date_end=get.get("dateEnd"),
        is_subst=is_subst,
        get_params=get
    )
    req_status.add(status, "Не удалось получить диагностические сообщения")
    result["status"] = req_status.get_message()

    return JsonResponse(
            result,
            json_dumps_params={'ensure_ascii': False},
            status=req_status.get_number_status()
    )


@time_func.runtime_in_log
def last_meterings(request, assetId: int) -> object:
    """Возвращает последние значения сигналов для оборудования"""
    req_status = request_status.RequestStatus(True)
    get = request.GET

    api_actual_version = "2"
    get_api_version = get.get("version", api_actual_version)
    if get_api_version == "1":
        result, status = meter_use_cases.get_last_meterings_v1(assetId, get.get("lng"))
    elif get_api_version == api_actual_version:
        result, status = meter_use_cases.get_last_meterings_v2(assetId, get.get("lng"))
    else:
        result = {}
        status = False
        req_status.add(status, f"Неизвестная версия API = {get_api_version}")

    req_status.add(status, "Не удалось получить последния значения сигналов "
                   f"для оборудования с {assetId = }")
    result["status"] = req_status.get_message()

    return JsonResponse(
            result,
            json_dumps_params={'ensure_ascii': False},
            status=req_status.get_number_status()
    )


@time_func.runtime_in_log
def meterings_for_charts(request, assetId: int, tab: str) -> object:
    """Возвращает значения сигналов за временной диапазон для графиков"""
    req_status = request_status.RequestStatus(True)
    get = request.GET
    result, status = meter_use_cases.get_meterings_for_charts(assetId,
                                                              get.get("dateStart"),
                                                              get.get("dateEnd"),
                                                              tab,
                                                              get.get("signals"),
                                                              get.get("lng"))
    req_status.add(status, "Не удалось получить значения сигналов "
                   f"для оборудования с {assetId = }")
    result["status"] = req_status.get_message()

    return JsonResponse(
            result,
            json_dumps_params={'ensure_ascii': False},
            status=req_status.get_number_status()
    )


@time_func.runtime_in_log
def rd_table(request, assetId: int) -> object:
    """Возвращает статусы превышения лимитов отношений газов по методике РД"""
    req_status = request_status.RequestStatus(True)
    get = request.GET
    result, status = meter_use_cases.get_rd_table(assetId, get.get("lng"))
    req_status.add(status, "Не удалось получить значения статусов превышения "
                   "лимитов отношений газов по методике РД "
                   f"для оборудования с {assetId = }")
    result["status"] = req_status.get_message()

    return JsonResponse(
            result,
            json_dumps_params={'ensure_ascii': False},
            status=req_status.get_number_status()
    )


@time_func.runtime_in_log
def duval_triangle(request, assetId: int) -> object:
    """Возвращает отношения концентраций газов по методу треугольника Дюваля"""
    req_status = request_status.RequestStatus(True)
    get = request.GET
    result, status = meter_use_cases.get_duval_triangle(assetId,
                                                        get.get("dateStart"),
                                                        get.get("dateEnd"))
    req_status.add(status, "Не удалось получить отношения концентраций газов "
                   "по методу треугольника Дюваля "
                   f"для оборудования с {assetId = }")
    result["status"] = req_status.get_message()

    return JsonResponse(
            result,
            json_dumps_params={'ensure_ascii': False},
            status=req_status.get_number_status()
    )


@time_func.runtime_in_log
def duval_pentagon(request, assetId: int) -> object:
    """
    Возвращает координаты точки статуса концентраций газов
    для пятиугольника Дюваля
    """
    req_status = request_status.RequestStatus(True)
    get = request.GET
    result, status = meter_use_cases.get_duval_pentagon(assetId,
                                                        get.get("dateStart"),
                                                        get.get("dateEnd"))
    req_status.add(status, "Не удалось получить координаты точки статуса "
                   "концентраций газов для пятиугольника Дюваля "
                   f"для оборудования с {assetId = }")
    result["status"] = req_status.get_message()

    return JsonResponse(
            result,
            json_dumps_params={'ensure_ascii': False},
            status=req_status.get_number_status()
    )


@time_func.runtime_in_log
def rd_nomogram(request, assetId: int) -> object:
    """Возвращает данные диагностики по методу номограм"""
    req_status = request_status.RequestStatus(True)
    get = request.GET
    result, status = meter_use_cases.get_rd_nomogram(assetId,
                                                     lang=get.get("lng"),
                                                     use_template=USE_DIAG_TEMPLATE)
    req_status.add(status, "Не удалось получить данные диагностики по методу номограм "
                   f"для оборудования с {assetId = }")
    result["status"] = req_status.get_message()

    return JsonResponse(
            result,
            json_dumps_params={'ensure_ascii': False},
            status=req_status.get_number_status()
    )


@time_func.runtime_in_log
def forecast_3d(request, assetId: int) -> object:
    """Возвращает данные 3D прогноза концентраций"""
    req_status = request_status.RequestStatus(True)
    get = request.GET
    result, status = meter_use_cases.get_forecast_3d(assetId,
                                                     lang=get.get("lng"))
    req_status.add(status, "Не удалось получить данные 3D прогноза "
                   f"для оборудования с {assetId = }")
    result["status"] = req_status.get_message()

    return JsonResponse(
            result,
            json_dumps_params={'ensure_ascii': False},
            status=req_status.get_number_status()
    )


@time_func.runtime_in_log
def hysteresis(request, assetId: int, tab: str) -> object:
    """Возвращает данные для графика гистерезиса"""
    req_status = request_status.RequestStatus(True)
    get = request.GET
    result, status = meter_use_cases.get_hysteresis(assetId,
                                                    get.get("dateStart"),
                                                    get.get("dateEnd"),
                                                    tab,
                                                    get.get("lng"))
    req_status.add(status, "Не удалось получить значения сигналов "
                   f"для оборудования с {assetId = }")
    result["status"] = req_status.get_message()

    return JsonResponse(
            result,
            json_dumps_params={'ensure_ascii': False},
            status=req_status.get_number_status()
    )


@time_func.runtime_in_log
def diag_mess_to_file(request, substId: int) -> object:
    """Создает файл экспорта диаг. сообщений"""
    req_status = request_status.RequestStatus(True)
    get = request.GET
    if not isinstance(get, dict):
        get = {}
    else:
        get = dict(get.items())
    get["use_template"] = USE_DIAG_TEMPLATE
    result = {}
    diag_messages, file_name, status = diagmsg_use_cases.get_subst_diag_messages_for_export(
        subst_id=substId,
        date_start=get.get("dateStart"),
        date_end=get.get("dateEnd"),
        get_params=get,
        lang=get.get("lng")
    )
    req_status.add(status,
                   "Не удалось получить диаг. сообщения для экспорта в файл")
    status, file_name = export_use_cases.data_to_file(
        get, file_name, "diag_messages", diag_messages)
    req_status.add(status,
                   "Не удалось создать файл диаг. сообщений")

    result["status"] = req_status.get_message()
    result["file_name"] = file_name
    return JsonResponse(
        result,
        json_dumps_params={'ensure_ascii': False},
        status=req_status.get_number_status()
    )


@time_func.runtime_in_log
def passport_to_file(request, assetId: int) -> object:
    """Создает файл экспорта паспорта"""
    req_status = request_status.RequestStatus(True)
    get = request.GET
    result = {}
    data, status = meter_use_cases.get_passport_data(assetId, get.get("lng"))
    req_status.add(status,
                   "Не удалось получить паспортные данные для экспорта в файл")
    file_name = "passport"
    status, file_name = export_use_cases.data_to_file(
        get, file_name, "pdata", data)
    req_status.add(status,
                   "Не удалось создать файл паспортных данных")

    result["status"] = req_status.get_message()
    result["file_name"] = file_name
    return JsonResponse(
        result,
        json_dumps_params={'ensure_ascii': False},
        status=req_status.get_number_status()
    )


@time_func.runtime_in_log
def diag_settings_to_file(request, assetId: int) -> object:
    """Создает файл экспорта лимитов и констант"""
    req_status = request_status.RequestStatus(True)
    get = request.GET
    result = {}
    data, status = meter_use_cases.get_diag_sett_data(assetId, get.get("lng"))
    req_status.add(status,
                   "Не удалось получить лимиты и константы для экспорта в файл")
    file_name = "limits_constants"
    status, file_name = export_use_cases.data_to_file(
        get, file_name, "lim&const", data)
    req_status.add(status,
                   "Не удалось создать файл лимитов и констант")

    result["status"] = req_status.get_message()
    result["file_name"] = file_name
    return JsonResponse(
        result,
        json_dumps_params={'ensure_ascii': False},
        status=req_status.get_number_status()
    )


def get_export_file(request) -> object:
    """Возвращает файл экспорта"""
    req_status = request_status.RequestStatus(True)
    result = {}
    response, status = export_use_cases.get_response_file(request.GET)

    if status is True:
        return response
    else:
        req_status.add(status, "Файла не существует")
        result["status"] = req_status.get_message()
        return JsonResponse(
            result,
            json_dumps_params={'ensure_ascii': False},
            status=req_status.get_number_status()
        )


@time_func.runtime_in_log
def geomap(request) -> object:
    """Возвращает данные для гео карты"""
    req_status = request_status.RequestStatus(True)
    get = request.GET
    result, status = geomap_use_cases.get_geomap(input_hash=get.get("hash"))
    req_status.add(status, "Не удалось получить данные гео карты")
    result["status"] = req_status.get_message()

    return JsonResponse(
            result,
            json_dumps_params={'ensure_ascii': False},
            status=req_status.get_number_status()
    )


@time_func.runtime_in_log
def signal_stats(request) -> object:
    """Возвращает статусы считывания сигнала с кодом `signal` за период."""

    query_params = request.GET

    # select GET query params
    date_start: str | None = query_params.get("dateStart") or None
    date_end: str | None = query_params.get("dateEnd") or None
    asset_guid: str | None = query_params.get("assetGuid") or None
    signal: str | None = query_params.get("signal") or None
    only_bad: bool = query_params.get("onlyBad") == "true"

    # validate GET query params
    if None in (date_start, date_end, asset_guid, signal):
        return JsonResponse(
            data={"err": "Query params: `assetGuid`, `dateStart`, `dateEnd`, `signal` must be specified!"},
            status=400,
        )

    try:
        start_timestamp: int = datestr_to_timestamp(date_start)
        end_timestamp: int = datestr_to_timestamp(date_end)
    except Exception as e:
        return JsonResponse(
            data={"err": f"Wrong format: `dateStart`, `dateEnd` must be in format `{DATE_FORMAT_STR}`! {e}"},
            status=400,
        )

    # get data from database
    db_stats: list[tuple] = stats_use_cases.get_signal_stats(
        asset_guid=asset_guid,
        signal=signal,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        only_bad=only_bad,
    )
    if db_stats is None:
        return JsonResponse(
            data={"err": f"Can't get last signals_stats for {asset_guid=}."},
            status=503,
        )

    # reorganize result data
    signal_stats = {
        signal: {},
    }
    if db_stats:
        x, y, messages = zip(*db_stats)
        signal_stats[signal]["timestamp"] = x

        signal_stats[signal]["x"] = list(map(timestamp_to_server_datestr, x))
        signal_stats[signal]["y"] = list(map(lambda item: int(item == "true"), y))
        signal_stats[signal]["messages"] = messages

    return JsonResponse(
        signal_stats,
        json_dumps_params={"ensure_ascii": False},
        safe=False,
        status=200,
    )


@time_func.runtime_in_log
def devices_stats(request, assetGuid: str) -> object:
    """Получить информацию о считывании сигналов по приборам для ассета с guid = `assetGuid`."""

    query_params = request.GET

    # select GET query params
    date_start: str | None = query_params.get("dateStart") or None
    date_end: str | None = query_params.get("dateEnd") or None

    try:
        start_timestamp: int = datestr_to_timestamp(date_start)
        end_timestamp: int = datestr_to_timestamp(date_end)
    except Exception as e:
        return JsonResponse(
            data={"err": f"Wrong format: `dateStart`, `dateEnd` must be in format `{DATE_FORMAT_STR}`! {e}"},
            status=400,
        )

    _asset_devices: list[dict] | None = stats_use_cases.get_asset_devices(asset_guid=assetGuid)
    if _asset_devices is None:
        return JsonResponse(
            data={"err": f"Can't get devices for {assetGuid=}."},
            status=503,
        )

    total_success_signals: list[dict] | None = stats_use_cases.get_signals_stats(
        asset_guid=assetGuid,
        device_ids=[device_id for device in _asset_devices if (device_id := device.get("id"))],
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
    )

    if total_success_signals is None:
        return JsonResponse(
            data={"err": f"Can't get signals stats for {assetGuid=}"},
            status=503,
        )

    signals_stats = []
    for signal_stat in total_success_signals:
        last_timestamp = signal_stat.get("last_timestamp")
        signals_stats.append(
            {
                "code": signal_stat.get("code"),
                "name": signal_stat.get("name"),
                "enabled": signal_stat.get("enabled"),
                "device": signal_stat.get("device"),
                "last_status": signal_stat.get("last_status") == 'true',
                "last_timestamp": None if last_timestamp is None else timestamp_to_server_datestr(last_timestamp),
                "last_message": signal_stat.get("last_message"),
                "success_statuses": signal_stat.get("success_statuses") or 0,
                "fail_statuses": signal_stat.get("fail_statuses") or 0,
            }
        )

    grouped_signals_stats: dict = {
        k: list(v)
        for k, v in
        groupby(signals_stats, lambda item: item.get("device"))
    }
    devices = [
        {
            "id": device.get("id"),
            "name": device.get("name"),
            "access_point": device.get("access_point"),
            "enabled": device.get("enabled"),
            "schedule": device.get("schedule"),
            "protocol": device.get("protocol"),
            "signals_stats": grouped_signals_stats.get(device.get("id"), [])
        }
        for device in _asset_devices
    ]

    return JsonResponse(
        data={
            "devices": devices,
        },
        json_dumps_params={"ensure_ascii": False},
        status=200,
    )


@time_func.runtime_in_log
def get_assets(request):
    """Запрос на получение всех ассетов с инфо о подстанции."""

    assets: list[dict] = stats_use_cases.get_substation_assets()
    if assets is None:
        return JsonResponse(
            data={"err": "Can't get assets."},
            status=503,
        )

    return JsonResponse(
        data={
            "assets": assets,
        },
        json_dumps_params={"ensure_ascii": False},
        status=200,
    )


@time_func.runtime_in_log
def get_models_stats_view(request):
    """ """

    query_params = request.GET
    asset_guid = query_params.get("assetGuid")
    date_start: str | None = query_params.get("dateStart") or None
    date_end: str | None = query_params.get("dateEnd") or None
    try:
        start_timestamp: int = datestr_to_timestamp(date_start)
        end_timestamp: int = datestr_to_timestamp(date_end)
    except Exception as e:
        return JsonResponse(
            data={"err": f"Wrong format: `dateStart`, `dateEnd` must be in format `{DATE_FORMAT_STR}`! {e}"},
            status=400,
        )

    if asset_guid is None:
        return JsonResponse(
            data={"err": "Query param: `assetGuid` must be specified"},
            status=400,
        )

    assets_models_stats: list[dict] | None = stats_use_cases.get_models_stats(
        asset_guid=asset_guid,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
    )
    if assets_models_stats is None:
        return JsonResponse(
            data={
                "err": "Something went wrong",
            },
            json_dumps_params={"ensure_ascii": False},
            status=503,
        )

    for asset_model_stats in assets_models_stats:
        asset_model_stats["timestamp"] = timestamp_to_server_datestr(asset_model_stats["timestamp"])
        asset_model_stats["model_start"] = timestamp_to_server_datestr(asset_model_stats["model_start"])
        asset_model_stats["model_end"] = timestamp_to_server_datestr(asset_model_stats["model_end"])

    return JsonResponse(
        data={
            "stats": assets_models_stats,
        },
        json_dumps_params={"ensure_ascii": False},
        status=200,
    )


@time_func.runtime_in_log
def get_model_stats_view(request):
    """ """

    query_params = request.GET
    asset_guid = query_params.get("assetGuid")
    model_code = query_params.get("modelCode")

    if not asset_guid or not model_code:
        return JsonResponse(
            data={"err": "Query params `assetGuid`, `modelCode` must be specified!"},
            status=400,
        )

    date_start: str | None = query_params.get("dateStart") or None
    date_end: str | None = query_params.get("dateEnd") or None
    try:
        start_timestamp: int = datestr_to_timestamp(date_start)
        end_timestamp: int = datestr_to_timestamp(date_end)
    except Exception as e:
        return JsonResponse(
            data={"err": f"Wrong format: `dateStart`, `dateEnd` must be in format `{DATE_FORMAT_STR}`! {e}"},
            status=400,
        )

    model_stats: list[dict] | None = stats_use_cases.get_model_stats(
        asset_guid=asset_guid,
        model_code=model_code,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
    )
    if model_stats is None:
        return JsonResponse(
            data={
                "err": "Something went wrong",
            },
            json_dumps_params={"ensure_ascii": False},
            status=503,
        )

    for model_stat in model_stats:
        model_stat["timestamp"] = timestamp_to_server_datestr(model_stat["timestamp"])
        model_stat["model_start"] = timestamp_to_server_datestr(model_stat["model_start"])

    return JsonResponse(
        data={
            "stats": model_stats,
        },
        json_dumps_params={"ensure_ascii": False},
        status=200,
    )


@time_func.runtime_in_log
def update_access_point(request, access_point_id: int):
    body = json.loads(request.body)
    updated_access_point_id: int | None = stats_use_cases.update_access_point(
        access_point_id=access_point_id,
        access_point=body,
    )

    if updated_access_point_id is None:
        return JsonResponse(
            data={
                "err": f"Access point with id={access_point_id} was not updated. data={body}",
            },
            json_dumps_params={"ensure_ascii": False},
            status=400,
        )

    return JsonResponse(
        data={
            "stats": "OK",
        },
        json_dumps_params={"ensure_ascii": False},
        status=200,
    )


def get_org_struct(request) -> object:
    """Возвращает организационную структуру объектов"""
    req_status = request_status.RequestStatus(True)
    result = subst_use_cases.get_company_struct()
    result["status"] = req_status.get_message()
    return JsonResponse(
            result,
            json_dumps_params={'ensure_ascii': False},
            status=req_status.get_number_status()
    )


@time_func.runtime_in_log
def get_notification_guide(request) -> object:
    """Возвращает справочный список уведомлений"""
    req_status = request_status.RequestStatus(True)
    get = request.GET
    result = subst_use_cases.get_conclusion_table(lang=get.get("lng"))
    result["status"] = req_status.get_message()
    return JsonResponse(
            result,
            json_dumps_params={'ensure_ascii': False},
            status=req_status.get_number_status()
    )


@time_func.runtime_in_log
def get_tabs_list(request) -> object:
    """Возвращает вкладки графиков доступные для типов оборудования"""
    req_status = request_status.RequestStatus(True)
    result = subst_use_cases.get_asset_type_tabs()
    result["status"] = req_status.get_message()
    return JsonResponse(
            result,
            json_dumps_params={'ensure_ascii': False},
            status=req_status.get_number_status()
    )


@time_func.runtime_in_log
def get_diagmsg_last(request) -> object:
    """Возвращает последние диаг. сообщения системы"""
    req_status = request_status.RequestStatus(True)
    get = request.GET
    result, status = diagmsg_use_cases.get_translation_latest(
        lang=get.get("lng"), use_template=USE_DIAG_TEMPLATE)
    req_status.add(status, "Ошибка формирования списка диаг. сообщений")
    result["status"] = req_status.get_message()
    return JsonResponse(
            result,
            json_dumps_params={'ensure_ascii': False},
            status=req_status.get_number_status()
    )
