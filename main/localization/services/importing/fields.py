from openpyxl.worksheet.worksheet import Worksheet

from .keys import PKey, ForeignKey


class CellOper:
    """Операции с ячейками xls файла"""
    @staticmethod
    def _get_cell_value(ws: Worksheet, row: int, column: int):
        """Получить значение ячейки с листа ws xls-файла."""
        val = ws.cell(row, column).value
        if isinstance(val, str):
            val = val.strip()
        return val


class Field(CellOper):
    """Обычное поле - столбец на странице xls файла."""
    def __init__(self, name: str, xls_column: int, is_pkey: bool = False,
                 is_defaults: bool = False, foreign_key: ForeignKey = False):
        self.__name = name
        self.__xls_column = xls_column
        self.__is_pkey = is_pkey
        self.__is_defaults = is_defaults
        self.__foreign_key = foreign_key

    def update_args(self, ws: Worksheet, row: int,
                    pkey: PKey, create_args: dict, update_args: dict,
                    cache: dict[str, dict]):
        value = self._get_value_or_object(ws, row, cache)
        self._update_pkey(pkey, value)
        self._update_args(create_args, update_args, value)

    def _get_value_or_object(self, ws: Worksheet, row: int, cache: dict[str, dict]):
        value = self._get_cell_value(ws, row, self.__xls_column)
        if self.__foreign_key:
            return self.__foreign_key.get_instance(cache, value)
        else:
            return value

    def _update_args(self, create_args: dict, update_args: dict, value):
        if self.__is_pkey is False:
            if self.__is_defaults:
                update_args[self.__name] = value
            else:
                create_args[self.__name] = value

    def _update_pkey(self, pkey: PKey, value):
        if self.__is_pkey:
            pkey.value = value


class CrossField(CellOper):
    """
    Поле в виде диапазона ячеек
    из списка столбцов (горизонтального поля) в xls файле.
    """
    def __init__(self, name: str, is_defaults: bool = False):
        self.__name = name
        self.__is_defaults = is_defaults

    def update_args(self, ws: Worksheet, row: int, column: int,
                    create_args: dict, update_args: dict):
        value = self._get_value_or_object(ws, row, column)
        self._update_args(create_args, update_args, value)

    def _get_value_or_object(self, ws: Worksheet, row: int, column: int):
        return self._get_cell_value(ws, row, column)

    def _update_args(self, create_args: dict, update_args: dict, value):
        if self.__is_defaults:
            update_args[self.__name] = value
        else:
            create_args[self.__name] = value


class HorizontalField(CellOper):
    """
    Поле в виде диапазона ячеек
    из определенной строки стриницы из xls файла.
    """
    def __init__(self, name: str, xls_row: int, cell_range: list[int],
                 cross_field: CrossField,
                 is_defaults: bool = False, foreign_key: ForeignKey = False):
        self.__name = name
        self.__xls_row = xls_row
        self.__cell_range = cell_range
        self.__cross_field = cross_field
        self.__is_defaults = is_defaults
        self.__foreign_key = foreign_key

    def get_columns(self):
        return range(self.__cell_range[0], self.__cell_range[1] + 1)

    def update_args(self, ws: Worksheet, row: int, column: int,
                    create_args: dict, update_args: dict,
                    cache: dict[str, dict]):
        value = self._get_value_or_object(ws, column, cache)
        self._update_args(create_args, update_args, value)
        self.__cross_field.update_args(ws, row, column,
                                       create_args, update_args)

    def _get_value_or_object(self, ws: Worksheet, column: int,
                             cache: dict[str, dict]):
        value = self._get_cell_value(ws, self.__xls_row, column)
        if self.__foreign_key:
            return self.__foreign_key.get_instance(cache, value)
        else:
            return value

    def _update_args(self, create_args: dict, update_args: dict, value):
        if self.__is_defaults:
            update_args[self.__name] = value
        else:
            create_args[self.__name] = value
