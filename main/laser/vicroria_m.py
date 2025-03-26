import logging
import requests

from main.settings import VM_ADDRESS, VM_PREFIX


logger = logging.getLogger(__name__)


def get_timestamps_of_last_processed_data():
    """
    Возвращает данные о метках времени последних данных обработанных сервисом
    диагностики в разрезе активов.
    """
    # metric_name = f'{VM_PREFIX}_main_models_status'
    metric_name = 'main_models_status'
    QUERY = f"max(tlast_over_time({metric_name}[30y])) by (asset)"
    params = {"query": QUERY}
    result = []
    try:
        response = requests.get(f"{VM_ADDRESS}/api/v1/query", params=params)
    except Exception as ex:
        logger.error(f"Ошибка запроса к VictoriaMetrics {response.request.url = }, {ex}")
        return result
    else:
        res = response.json()
        return get_data_from_response(res)


def get_last_value_signals(
        asset_guid: str,
        codes: list[str],
        timestamp_start: float | None = None,
        step: str = '30y'):
    """
    Возвращает последние значения сигналов
    для данного актива и списка кодов сигналов.
    """
    metric_name = f'{VM_PREFIX}_signals_value'
    QUERY = f"{metric_name}{{asset='{asset_guid}', signal=~'{'|'.join(codes)}'}}"
    if timestamp_start:
        QUERY = QUERY + f" @ {timestamp_start}"
    params = {"query": QUERY, "step": step}
    try:
        response = requests.get(f"{VM_ADDRESS}/api/v1/query", params=params)
    except Exception as ex:
        logger.error(f"Ошибка запроса к VictoriaMetrics {VM_ADDRESS}: {ex}")
        return None, False
    else:
        res = response.json()
        return get_data_from_response(res), True


def get_data_from_response(response: dict):
    status = response.get("status")
    result_type = response.get("data", {}).get("resultType")
    error_type = ''
    error_text = ''
    data = []
    logger.info(f"{status = }, {result_type = }")
    if status.lower() == "error":
        error_type = response.get("errorType")
        error_text = response.get("error")
        logger.error(f"{error_type = }\n{error_text = }")
    else:
        data = response.get("data", {}).get("result")
    return data
