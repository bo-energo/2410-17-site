class InputParams:
    __pagin_keys = {
            "offset": "diagNumStart",
            "limit": "diagCount",
        }
    __other_keys = {
        "diag_type": "diagType",
        "search": "search",
        "order_field": "orderField",
        "order_type": "orderType",
        "lang": "lng",
        "use_template": "use_template",
    }

    def __init__(self, get_params: dict):
        self._params = self.web_to_db_params(get_params)

    def get_params_without_pagination(self):
        return {
            key: self._params.get(key)
            for key in self.__other_keys.keys()
        }

    def get_pagination_params(self):
        return {
            key: self._params.get(key)
            for key in self.__pagin_keys.keys()
        }

    @classmethod
    def web_to_db_params(cls, get_params: dict):
        """Возвращает словарь значений параметров для запроса объектов из БД"""
        return {output_key: get_params.get(input_key)
                for output_key, input_key in {**cls.__other_keys, **cls.__pagin_keys}.items()}
