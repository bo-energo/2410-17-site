from datetime import datetime

from main.settings import TIME_ZONE


class SelectDiagMessConfig:
    """Класс конфигурации запроса диагностических сообщений"""
    __convert_types = {"str": str, "int": int, "float": float}

    keys = {
        "offset": "diagNumStart",
        "limit": "diagCount",
        "diag_type": "diagType",
        "search": "search",
        "order_field": "orderField",
        "order_type": "orderType",
    }

    def __init__(self, main_fields: dict, query_params: dict):
        self._main_fields = main_fields
        self._group_search = self.__clear(query_params.get("diag_type"), "str")
        self._search = self.__clear(query_params.get("search"), "str")
        self._order_field = self.__clear(query_params.get("order_field"), "str")
        self._order_type = self.__clear(query_params.get("order_type"), "str")
        self._offset = self.__clear(query_params.get("offset"), "int")
        self._limit = self.__clear(query_params.get("limit"), "int")

    @classmethod
    def __clear(cls, param, output_type: str):
        if param is None:
            return param
        if output_type in cls.__convert_types:
            if isinstance(param, cls.__convert_types[output_type]):
                return param
            else:
                try:
                    return cls.__convert_types[output_type](param)
                except Exception:
                    return None

    def get_additional_filtering(self, date_start: datetime, date_end: datetime):
        result = []
        if date_start:
            result.append(f"AND dm.timestamp >= {date_start.timestamp()}")
        if date_end:
            result.append(f"AND dm.timestamp <= {date_end.timestamp()}")
        if self._group_search == "sys":
            self._group_search = "system"
        if self._group_search:
            if self._group_search == "all":
                result.append("AND dm.group IN ('diag', 'system')")
            else:
                result.append(f"AND dm.group = '{self._group_search}'")
        if self._search:
            result.append("AND (")
            result.append(f"{self._main_fields.get('message')} ILIKE '%{self._search}%'")
            result.append(f"OR a.name ILIKE '%{self._search}%'")
            result.append(f"OR to_char(timezone('{TIME_ZONE}', to_timestamp(timestamp)),"
                          f"'YYYY.MM.DD HH24:MI:SS') ILIKE '%{self._search}%'")
            result.append(")")
        return result

    def get_ordering(self):
        db_field = self._main_fields.get(self._order_field, "timestamp")
        if self._order_type and self._order_type.upper() in ("ASC", "DESC"):
            order_type = self._order_type
        else:
            order_type = "ASC"
        return f"ORDER BY {db_field} {order_type}"

    def get_slicing(self):
        """Получить срез результата запроса"""
        if self._get_limit() is None:
            return f"OFFSET {self._get_offset()}"
        else:
            return f"LIMIT {self._get_limit()} OFFSET {self._get_offset()}"

    def _get_offset(self):
        if self._offset is None:
            return 0
        elif self._offset > 0:
            return self._offset
        else:
            return 0

    def _get_limit(self):
        if self._limit and self._limit <= 0:
            return None
        else:
            return self._limit
