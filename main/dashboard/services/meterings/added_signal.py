import logging
from typing import Callable, List, Any
from main.settings import ROUND_NDIGIT

logger = logging.getLogger(__name__)


class AddedSignal:
    def __init__(self, code: str, output_key: str, format_func: Callable, default=None):
        self.__code = code
        self.__output_key = output_key
        self.__format_func = format_func
        self.__default = default

    def get_code(self):
        return self.__code

    @classmethod
    def get_codes(cls, signals: list['AddedSignal']):
        return [s.get_code() for s in signals]

    def get_output_key(self):
        return self.__output_key

    def get_formatted_value(self, value: Any):
        if isinstance(self.__format_func, Callable):
            try:
                result = self.__format_func(value)
            except Exception:
                logger.exception(f"Ошибка при форматировании {self.__code} = {value}")
                result = self.__default
        else:
            result = value
        if isinstance(result, float):
            return round(result, ROUND_NDIGIT)
        else:
            return result

    @classmethod
    def from_args_list(cls, args: List[List]):
        return [AddedSignal(code, key, func) for code, key, func in args]
