import logging
import json
import requests
from datetime import datetime
from functools import lru_cache

from main.settings import VML_ADDRESS, VML_PROJECT_ID
from dashboard.utils.time_func import runtime_in_log
from .diag_config import QueryConfig


logger = logger = logging.getLogger(__name__)


class VMDiagMsgManager:
    """VictoriaLogs менеджер диагностических сообщений"""

    @classmethod
    @runtime_in_log
    @lru_cache(maxsize=10)
    def per_interval(cls, obj_id: int, date_start: datetime, date_end: datetime,
                     query_config: QueryConfig = None):
        """
        Возвращает диагностические сообщения для
        актива в интервале [date_start, date_end]

        Parameters:
        ---
        - obj_id: int - идентификатор объекта, для которого выбираются сообщения;
        Генерирует исключение при ошибках запроса или парсинга результата.
        """
        if not query_config:
            query_config = QueryConfig()

        url_query = f"{VML_ADDRESS}/select/logsql/query"
        headers = {'projectid': VML_PROJECT_ID or 0}
        query = " | ".join(
            (
                val
                for val in (
                    query_config.get_group_filter(obj_id),
                    query_config.get_pipe_fields())
                if val))
        params = {"query": query, "start": date_start.timestamp(), "end": date_end.timestamp()}
        query_descripts = [
            f"URL = {url_query}",
            f"Заголовок HTTP запроса = {headers}",
            f"VLogs запрос = {query}",
            f"Параметры запроса = {params}",]
        try:
            # raise ValueError("Тестовое исключение при запросе")
            response = requests.post(url_query, headers=headers, data=params)
        except Exception as ex:
            message_chanks = [
                    "Ошибка запроса диаг сообщений.",
                    *query_descripts,
                    str(ex)]
            logger.error("\n".join(message_chanks))
            raise ex
        else:
            res = []
            count_rec = 0
            errors = {}
            for rec in response.iter_lines():
                count_rec += 1
                try:
                    # raise ValueError("Тестовое исключение при парсинге")
                    row_data = json.loads(rec)
                except Exception as ex:
                    str_ex = str(ex)
                    if str_ex not in errors:
                        errors[str_ex] = 0
                    errors[str_ex] += 1
                else:
                    res.append(row_data)
            if errors:
                message_chanks = [
                    "Ошибки парсинга результата запроса диаг сообщений.",
                    *query_descripts,
                    f"Получено записей = {count_rec}"]
                count_all_errors = 0
                for key, count in errors.items():
                    message_chanks.append(f"[Error]: {key}. Кол-во: {count}")
                    count_all_errors += count
                message = "\n".join(message_chanks)
                if count_rec == count_all_errors:
                    raise ValueError(message)
                else:
                    logger.warning(message)
            status = True
        return res, status

    @classmethod
    def _get_condition_select_assets(cls, obj_id: int, is_subst: bool = True):
        """Возвращает условие отбора активов при запросе диаг. сообщений."""
        if is_subst is True:
            return f"a.substation_id = {obj_id}"
        else:
            return f"a.id = {obj_id}"
