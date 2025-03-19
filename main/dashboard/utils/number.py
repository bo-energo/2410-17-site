import logging
from json import loads


logger = logging.getLogger(__name__)


class Numeric:
    @classmethod
    def round_float(cls, str_number: str | float, ndigit: int):
        """
        Округляет вещественное число.
        Если str_number типа str, то результат тоже будет типа str.
        Если при округлении возникла ошибка, возвращает значение без изменений.
        """
        if isinstance(str_number, str):
            try:
                if ndigit > 0:
                    return str(round(float(str_number), ndigit))
                else:
                    return str(round(float(str_number)))
            except Exception:
                pass
        elif isinstance(str_number, float):
            try:
                if ndigit > 0:
                    return round(str_number, ndigit)
                else:
                    return round(str_number)
            except Exception:
                pass
        return str_number

    @classmethod
    def form_float(cls, str_number: str | float, ndigit: int, default=None) -> str | float:
        """
        Округляет вещественное число.
        Если округление прошло успешно, то возвращает float,
        иначе возвращает default.
        """
        try:
            return round(float(str_number), ndigit)
        except Exception:
            return default

    @classmethod
    def convert_manual_value(cls, value: str):
        """
        Производит попытку конвертации входного значения в число, список или
        словарь, если попытка неудачна, то возвращается исходное значение.
        """
        try:
            return loads(value)
        except Exception:
            logger.error(f"Некорректное значение для json конвертации: '{value}'")

        return value
