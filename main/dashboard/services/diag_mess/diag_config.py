class Config:
    """Родительский класс конфигуратора обработки диаг сообщений"""
    _convert_types = {"str": str, "int": int, "float": float}

    _all_group_search = "all"

    @classmethod
    def _clear(cls, param, output_type: str):
        if param is None:
            return param
        if output_type in cls._convert_types:
            if isinstance(param, cls._convert_types[output_type]):
                return param
            else:
                try:
                    return cls._convert_types[output_type](param)
                except Exception:
                    return None


class QueryConfig(Config):
    """Класс конфигуратора запроса диаг сообщений"""

    def __init__(self, **kwargs):
        self._group_search = self._clear_group(kwargs.get("diag_type"))

    def get_group_filter(self, asset):
        filter_parts = []
        if self._group_search:
            if self._group_search == self._all_group_search:
                group_search = '"group":("diag" OR "system")'
            else:
                group_search = f'"group":"{self._group_search}"'
            filter_parts.append(group_search)
        if asset:
            filter_parts.append(f'"asset":"{asset}"')
        return " AND ".join(filter_parts)

    def get_pipe_fields(self):
        return 'fields asset,level,param_groups,group,id_tab,message_ids,signals,_time,_msg'

    @classmethod
    def _clear_group(cls, value):
        value = cls._clear(value, "str")
        if isinstance(value, str):
            value = value.lower()
        if value == "sys":
            return "system"
        else:
            return value

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        if self is other:
            return True
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        return hash(self._group_search)


class ProcessedConfig(Config):
    """Класс конфигуратора обработки диаг сообщений из БД"""

    def __init__(self, **kwargs):
        self._search = self._clear(kwargs.get("search"), "str")
        self._order_field = self._clear_order_field(kwargs.get("order_field"))
        self._order_type = self._clear_order_type(kwargs.get("order_type"))
        self._lang = self._clear(kwargs.get("lang", "ru"), "str")

    def get_order_field(self):
        return self._order_field

    def is_order_reverse(self):
        if self._order_type == "desc":
            return True
        else:
            return False

    @classmethod
    def _clear_order_field(cls, value):
        value = cls._clear(value, "str")
        if not isinstance(value, str):
            value = ""
        value = value.lower()
        if value == "asset":
            return "asset_name"
        if value == "message":
            return value
        else:
            return "_time"

    @classmethod
    def _clear_order_type(cls, value):
        value = cls._clear(value, "str")
        if isinstance(value, str):
            value = value.lower()
        if value == "desc":
            return value
        else:
            return ""

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        if self is other:
            return True
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        return hash((self._search, self._order_field, self._order_type, self._lang))


class PaginationConfig(Config):
    """Класс конфигуратора пагинации диаг сообщений"""

    def __init__(self, **kwargs):
        self._offset: int | None = self._clear(kwargs.get("offset"), "int")
        self._limit: int | None = self._clear(kwargs.get("limit"), "int")

    def get_start_slice(self):
        if self._offset and self._offset > 0:
            return self._offset
        else:
            return 0

    def get_end_slice(self):
        if self._limit is not None and self._limit >= 0:
            return self.get_start_slice() + self._limit
        else:
            return None
