import logging
import requests

from copy import deepcopy
from dashboard.models import Assets
from dashboard.utils import request_status, time_func
from dashboard.services.commons.meterings_manager import MeteringsManager
from dashboard.services.commons.assets_manager import AssetsManager
from laser.settings import LASER_SERVICE
from laser.models import LoadedData
from laser import vicroria_m as vmet
from laser.diag_signals import sgn_needed_for_diag


logger = logging.getLogger(__name__)
STATUS_ITS_LOADED = 1
STATUS_IN_PROCESS = 2
STATUS_PROCESSING_COMPLETE = 3
STATUS_NOT_DATA = 4
STATUS_PROCESSING_ERROR = 5


def check_diag_settings(asset_guid: str):
    """
    Возвращает результат проверки наличия значений сигналов,
    обязательных для успешной диагностики.
    """
    empty_signals_key = "empty_signals"
    result = {empty_signals_key: []}
    sgn_for_diag = deepcopy(sgn_needed_for_diag)
    req_status = request_status.RequestStatus(True)

    assets = AssetsManager.get_by_guids((asset_guid,))
    if assets:
        asset = assets[0]
    else:
        req_status.add(
            False,
            "Не найдено оборудование. Проверьте что в системе присутствует оборудование с GUID = {asset_guid}")
        return result, req_status
    data, status = MeteringsManager.get_last_meterings(
        asset,
        sgn_for_diag.keys())
    if not status:
        req_status.add(False, "Ошибка запроса к БД. Обратитесь к разработчикам.")
        return result, req_status
    for ts in data:
        if len(ts) > 2:
            sgn_for_diag.pop(ts[1])
        else:
            continue
    result[empty_signals_key] = [[code, name] for code, name in sorted(sgn_for_diag.items())]
    return result, req_status


def get_all_loaded_data_info():
    """Возвращает данные о всех загрузках измерений с прибора"""
    req_status = request_status.RequestStatus(True)
    result: list[dict] = []
    try:
        loadings = LoadedData.objects.all().order_by("-id")
    except Exception as ex:
        logger.error(f"Не удалось получить информацию о загрузках из БД. {ex}")
        req_status.add(False, "Ошибка БД. Сообщите разработчикам")
    else:
        timestamps_of_last_processed_data = _get_timestamp_by_asset(
            vmet.get_timestamps_of_last_processed_data())
        for loaded_data in loadings:
            timestamp_lpd = timestamps_of_last_processed_data.get(loaded_data.asset_guid)
            loaded_data = _calc_state_loaded_data(loaded_data, timestamp_lpd)
            percent_processed = _calc_percent_processed_loaded_data(loaded_data, timestamp_lpd)
            result.append(_formatting_loaded_data_info(loaded_data, percent_processed))
    return {"loading": result}, req_status


def get_loaded_data_info(id: int):
    """Возвращает информацию о загрузке c id = 'id'"""
    req_status = request_status.RequestStatus(True)
    try:
        loaded_data = LoadedData.objects.get(id=id)
    except LoadedData.DoesNotExist as ex:
        mess = f"Загрузка данных с {id =} не найдена в базе данных."
        logger.error(f"{mess} {ex}")
        req_status.add(False, mess)
        result = {}
    except Exception as ex:
        logger.error(f"Не удалось получить информацию о загрузке данных с {id =} из БД. {ex}")
        req_status.add(False, "Ошибка базы данных. Сообщите разработчикам")
        result = {}
    else:
        timestamps_of_last_processed_data = _get_timestamp_by_asset(
            vmet.get_timestamps_of_last_processed_data())
        timestamp_lpd = timestamps_of_last_processed_data.get(loaded_data.asset_guid)
        loaded_data = _calc_state_loaded_data(loaded_data, timestamp_lpd)
        percent_processed = _calc_percent_processed_loaded_data(loaded_data, timestamp_lpd)
        result = _formatting_loaded_data_info(loaded_data, percent_processed)
    return {"loaded_data": result}, req_status


def online():
    """Возвращает IP подключенного прибора Laser"""
    req_status = request_status.RequestStatus(True)
    result = {"ip": ""}
    try:
        response = requests.get(f"{LASER_SERVICE}/lasers", timeout=20)
    except Exception as ex:
        logger.error(f"Ошибка выполнения запроса '{LASER_SERVICE}/lasers'. {ex}")
        req_status.add(False, "Проверьте работу сервиса интеграции с газоанализатором Лазер")
        return result, req_status

    if response.status_code != 200:
        req_status.add(False, "Проверьте работу сервиса интеграции с газоанализатором Лазер")
        return result, req_status

    try:
        ip = response.json()["lasers"][0]["ip"]
        if not ip:
            raise ValueError("IP не должен быть пустым")
    except IndexError:
        req_status.add(False, "Газоанализатор Лазер не обнаружен. Проверьте подключение")
    except Exception as ex:
        logger.error(f"Ошибка чтения результата запроса '{LASER_SERVICE}/lasers'. {ex}")
        req_status.add(False, "Ошибка чтения данных. Сообщите разработчикам.")
    else:
        result["ip"] = ip
    return result, req_status


def read_data(date_start: str, date_end: str, asset_guid: str, ip: str):
    """Прочитать данные с Лазер и загрузить в шину"""
    req_status = request_status.RequestStatus(True)
    timestamp_start = time_func.normalize_date(date_start)
    timestamp_end = time_func.normalize_date(date_end)
    result = {}
    if not date_start or not date_end or not asset_guid or not ip:
        logger.error(
            f"Параметры для запроса '{LASER_SERVICE}/read-data' не могут быть пустыми. "
            f"({timestamp_start = }  {timestamp_end = }  {asset_guid = }  {ip = })")
        req_status.add(False,  "Недостаточно данных для выполнения запроса. Сообщите разработчикам.")
        return result, req_status
    body = {
        "from_unix_utc_timestamp": timestamp_start.timestamp(),
        "to_unix_utc_timestamp": timestamp_end.timestamp(),
        "asset": asset_guid,
        "ip": ip
    }

    try:
        response = requests.post(f"{LASER_SERVICE}/read-data", json=body, timeout=300)
    except Exception as ex:
        logger.error(f"Ошибка выполнения запроса '{LASER_SERVICE}/read-data', {body = }. {ex}")
        req_status.add(False, "Проверьте работу сервиса интерграции с газоанализатором Лазер")
        return result, req_status

    try:
        response_data = response.json()
    except Exception as ex:
        logger.error(
            f"Ошибка чтения результата запроса '{LASER_SERVICE}/read-data', {body = }. {ex}")
        response_data = response.text

    if response.status_code != 200:
        logger.error(
            f"Запрос '{LASER_SERVICE}/lasers', {body = }. {response.status_code = }, {response_data = }")
        req_status.add(False, "Не удалось прочитать данные измерений с газоанализатора Лазер.")
        return result, req_status

    loaded_data_info = _get_kwargs_loaded_data_info(response_data)
    if not loaded_data_info:
        logger.error(
            f"Ошибка чтения результата запроса '{LASER_SERVICE}/read-data', {body = }")
        req_status.add(False, "Ошибка чтения данных. Сообщите разработчикам.")
        return result, req_status

    loaded_data = LoadedData(**loaded_data_info)
    if loaded_data.data_timestamp_start is None or loaded_data.data_timestamp_end is None:
        logger.warning(
            f"Запросом '{LASER_SERVICE}/read-data' в шину ничего не записано, {body = }")
        req_status.add(
            False,
            f"Не найдены данные для оборудования с guid = {asset_guid} за диапазон [{date_start}, {date_end}]")
        return result, req_status

    loaded_data.status = 1
    loaded_data = _save_loaded_data_info(loaded_data)
    if not loaded_data:
        req_status.add(
            False,
            "Не удалось сохранить информацию о загруженных с прибора данных. Сообщите разработчикам.")
    else:
        result["loaded_data_id"] = loaded_data.id
    return result, req_status


def _get_asset_name(asset_guid: str):
    """Возвращает имя актива согласно его GUID"""
    try:
        asset = Assets.objects.get(guid=asset_guid)
        if asset.substation and asset.substation.name:
            result = f"{asset.substation.name}, {asset.name}"
        else:
            result = asset.name
        return result
    except Exception as ex:
        logger.error(f"Не удалось определить имя оборудования. {ex}")
        return None


def _formatting_loaded_data_info(loading: LoadedData, percent_processed: int = None):
    """Возвращает отформатированную для фронта информацию о загрузке"""
    return {
                "id": loading.id,
                "asset_name": loading.asset_name,
                "asset_guid": loading.asset_guid,
                "date_start": loading.date_start,
                "date_end": loading.date_end,
                "status": loading.status,
                "percent_processed": percent_processed
            }


def _calc_percent_processed_loaded_data(loaded_data: LoadedData, timestamp_lpd: float = None):
    """
    Возвращает процент обработки загрузки данных.
    """
    # если загрузка имеет один из статусов 'Обработаны''Нет данных', 'Ошибка при обработке',
    # процент обработки = 100
    if loaded_data.status in (STATUS_PROCESSING_COMPLETE, STATUS_NOT_DATA, STATUS_PROCESSING_ERROR):
        percent_processed = 100
    # если загрузка имеет статус 'Загружены в шину', процент обработки = 0
    elif loaded_data.status == STATUS_ITS_LOADED:
        percent_processed = 0
    # если нет метки времени для asset_guid загрузки, процент обработки = None
    elif timestamp_lpd is None:
        percent_processed = None
    # если загрузка имеет статус 'В обработке', рассчитываем процент обработки
    elif loaded_data.status == STATUS_IN_PROCESS:
        loaded_data_time_delta = loaded_data.data_timestamp_end - loaded_data.data_timestamp_start
        processed_data_time_delta = timestamp_lpd - loaded_data.data_timestamp_start
        # если дата обработанных данных меньше начальной даты загруженных данных, процент обработки = 0
        if processed_data_time_delta < 0:
            percent_processed = 0
        # если диапазон времени загруженных данных менбше или равен 0, процент обработки = None
        elif loaded_data_time_delta <= 0:
            percent_processed = None
        else:
            percent_processed = int(processed_data_time_delta / loaded_data_time_delta * 100)
    else:
        percent_processed = None
    return percent_processed


def _calc_state_loaded_data(loaded_data: LoadedData, timestamp_lpd: float = None):
    """
    Возвращает загрузку данных с обновленным статусом.
    """
    # если загрузка имеет один из статусов 'Обработаны''Нет данных', 'Ошибка при обработке',
    # возвращаем ее без изменений
    if loaded_data.status in (STATUS_PROCESSING_COMPLETE, STATUS_NOT_DATA, STATUS_PROCESSING_ERROR):
        return loaded_data
    # если нет метки времени для asset_guid загрузки, возвращаем загрузку без изменений
    elif timestamp_lpd is None:
        return loaded_data
    # если конечная метка времени данных в загрузке меньше или равна
    # метке времени последних обработанных данных для asset_guid загрузки,
    # статус загрузки меняем на 'Обработаны'
    elif loaded_data.data_timestamp_end <= timestamp_lpd:
        loaded_data.status = STATUS_PROCESSING_COMPLETE
        _save_loaded_data_info(loaded_data)
        return loaded_data
    # если начальная метка времени данных в загрузке меньше или равна
    # метке времени последних обработанных данных для asset_guid загрузки,
    # статус загрузки меняем на 'Обработаны', рассчитываем процент обработки
    elif loaded_data.data_timestamp_start <= timestamp_lpd and loaded_data.status != STATUS_IN_PROCESS:
        # Здесь не будет ошибки деления на ноль, так как
        # если data_timestamp_end == data_timestamp_start, то выполнится условие выше
        loaded_data.status = STATUS_IN_PROCESS
        _save_loaded_data_info(loaded_data)
        return loaded_data
    # во всех прочих случаях возвращаем загрузку без изменений
    else:
        return loaded_data


def _save_loaded_data_info(loaded_data: LoadedData):
    """Сохраняет информацию о загрузке в БД"""
    loaded_data.asset_name = _get_asset_name(loaded_data.asset_guid)
    try:
        loaded_data.save()
    except Exception as ex:
        logger.error(
            f"Ошибка сохранения в базу информации о загруженных с прибора данных. {ex}")
        loaded_data = None
    return loaded_data


def _get_kwargs_loaded_data_info(input_data: dict):
    """
    Возвращает словарь аргументов для сохранения в БД информации
    о загруженных данных. При ошибке возвращает пустой словарь!
    """
    try:
        return {
            "asset_guid": input_data["asset"],
            "timestamp_start": input_data["from_unix_utc_timestamp"],
            "timestamp_end": input_data["to_unix_utc_timestamp"],
            "data_timestamp_start": input_data["data_from_unix_utc_timestamp"],
            "data_timestamp_end": input_data["data_to_unix_utc_timestamp"],
        }
    except Exception as ex:
        logger.error(
            f"Ошибка чтения входных данных', {input_data = }. {ex}")
        return {}


def _get_timestamp_by_asset(vm_data: list[dict]):
    """Возвращает метки времени в разрезе активов"""
    result = {}
    for ts in vm_data:
        guid = ts.get("metric", {}).get("asset")
        value = ts.get("value")
        if guid and isinstance(value, (tuple, list)) and len(value) > 1:
            result[guid] = float(value[1])
    return result
