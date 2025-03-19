import logging
from copy import deepcopy
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from django.db import models

from .keys import PKey
from .fields import Field, HorizontalField


logger = logging.getLogger(__name__)


class ImportManager:
    """Менеджер импорта данных из xls файла."""
    def __init__(self, model: models.Model, sheet_name: str, fields: list[Field],
                 horizontal_field: HorizontalField = None, cache: dict = None):
        self.__model = model
        self.__sheet_name = sheet_name
        self.__fields = fields
        self.__horizontal_field = horizontal_field
        self.__current_row = 2
        self.__cache = cache

    def _create_obj(self, pk: PKey, create_args: dict, update_args: dict):
        obj = None
        try:
            obj, created = self.__model.objects.update_or_create(**create_args, defaults=update_args)
        except Exception as ex:
            print(flush=True)
            logger.error(f"Ошибка создания/обновления экземпляра {self.__model}."
                         f"\n{create_args = };  {update_args = }\nEXCEPTION: {ex}")
        if obj is not None and isinstance(self.__cache, dict):
            if self.__sheet_name not in self.__cache:
                self.__cache[self.__sheet_name] = {}
            self.__cache[self.__sheet_name][pk.value] = obj

        print(".", end="", flush=True)

    def import_obj(self, ws: Worksheet):
        pk = PKey()
        create_args = {}
        update_args = {}
        for field in self.__fields:
            field.update_args(ws, self.__current_row, pk,
                              create_args, update_args, self.__cache)

        if not self.__horizontal_field:
            self._create_obj(pk, create_args, update_args)
        else:
            for column in self.__horizontal_field.get_columns():
                final_pk = deepcopy(pk)
                final_create_args = deepcopy(create_args)
                final_update_args = deepcopy(update_args)
                self.__horizontal_field.update_args(ws, self.__current_row, column,
                                                    final_create_args, final_update_args,
                                                    self.__cache)
                self._create_obj(final_pk, final_create_args, final_update_args)
        self.__current_row += 1

    def import_all(self, wb: Workbook):
        print(f"\nИмпорт {self.__model}:")
        if self.__sheet_name not in wb.sheetnames:
            logger.warning(f"В импортируемом файле не найден лист {self.__sheet_name}")
            return
        ws = wb[self.__sheet_name]
        while ws.cell(self.__current_row, 2).value is not None:
            self.import_obj(ws)

    def set_cache(self, cache: dict):
        self.__cache = cache
