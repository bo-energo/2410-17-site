import logging
from dataclasses import dataclass
from django.db import models


logger = logging.getLogger(__name__)


@dataclass
class PKey:
    value = None


class ForeignKey:
    def __init__(self, sheet_name: str, model: models.Model, find_field: str):
        self._sheet_name = sheet_name
        self._model = model
        self._find_field = find_field

    def get_instance(self, cache: dict[str, dict], value):
        if self._sheet_name and isinstance(cache, dict):
            instance = cache.get(self._sheet_name, {}).get(value)
        else:
            instance = None
        if instance is None:
            try:
                instance = self._model.objects.get(**{self._find_field: value})
            except Exception as ex:
                instance = None
                print(flush=True)
                logger.error(f"Ошибка запроса '{self._model._meta.verbose_name}' c условием '{self._find_field} = {value}'."
                             f"\nEXCEPTION: {ex}")
        return instance
