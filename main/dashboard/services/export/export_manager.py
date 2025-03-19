import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any
from django.http import HttpResponse

from main.settings import STATIC_ROOT

logger = logger = logging.getLogger(__name__)


@dataclass
class ExportSettings:
    """Класс настроек экспорта"""
    format: str = None
    supported: bool = False
    open_mode: str = "w"
    encoding: str = None
    newline: str = None
    kwargs: dict = None

    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = dict()


class ExportManager(ABC):
    """менеджер для создания файла экспорта"""

    def __init__(self, format, name_exp_file):
        self._format = self._get_format_settings(format)
        self._update_format_settings()
        name_exp_file = self._get_file_name_with_ext(name_exp_file)
        self._exp_file_path = self._get_file_path(name_exp_file)

#   --- Методы класса и статические методы ---
    @classmethod
    def get_response_with_file(cls, file_name: str):
        """Возвращает HttpResponse с присоединенным файлом экспорта"""
        file_path = cls._get_file_path(file_name)
        try:
            response_status = 200
            with file_path.open("rb") as fp:
                response = HttpResponse(fp.read(), status=response_status)
            file_type = "application/octet-stream"
            response["Content-Type"] = file_type
            response["Content-Length"] = str(os.stat(file_path).st_size)
            response["Content-Disposition"] = f"attachment; filename={file_path.name}"
            os.remove(file_path)
            return response, True
        except Exception:
            logger.exception("Не удалось создать HttpResponse с файлом экспорта")
            return None, False

    @classmethod
    def _get_file_path(cls, file_name):
        return STATIC_ROOT.joinpath('temp').joinpath(file_name)

#   --- Абстрактные методы ---
    @abstractmethod
    def _custom_checking_processed_data(self, processed_data) -> bool:
        """Возвращает корректность обработанных данных для экспорта"""
        pass

    @abstractmethod
    def _default_file_name(self):
        """Возвращает имя файла экспорта по умолчанию"""
        pass

    @abstractmethod
    def _get_data_for_write_to_file(self, processed_data) -> Any | None:
        """Возвращает файловые данные для записи"""
        pass

    @abstractmethod
    def _get_processed_data(self, input_data: dict) -> Any | None:
        """Возвращает обработанные данные для экспорта"""
        pass

    @abstractmethod
    def _update_format_settings(self, exp_sett: ExportSettings):
        """Обновляет объект конфигурации экспорта"""
        pass

#   --- Методы публичного интерфейса ---
    def create_file(self, input_data: Dict[str, Dict[str, Any]]):
        """Создает файл экспорта"""
        processed_data = self._get_processed_data(input_data)
        if not self._is_export_possible(processed_data):
            return False, None
        file_data = self._get_data_for_write_to_file(processed_data)
        if file_data is None:
            return False, None
        file_name = self._to_file(file_data)
        if file_name is None:
            return False, file_name
        else:
            return True, file_name

#   --- Приватные и защищённые методы ---
    def _get_file_name_with_ext(self, file_name):
        if not file_name:
            file_name = self._default_file_name()
        return f"{file_name}.{self._format.format}"

    def _get_format_settings(self, format: str):
        """Возвращает объект конфигурации экспорта"""
        if isinstance(format, str):
            format = format.lower()
        if format == "html":
            exp_sett = ExportSettings(
                format="html",
                supported=True,
                open_mode="w",
                encoding="UTF8")
        elif format == "csv":
            exp_sett = ExportSettings(
                format="csv",
                supported=True,
                open_mode="w",
                encoding="UTF8",
                newline='',
                kwargs={"delimiter": ';'})
        elif format == "xls":
            exp_sett = ExportSettings(
                format="xls",
                supported=True,
                open_mode="wb")
        elif format == "pdf":
            exp_sett = ExportSettings(
                format="pdf",
                supported=True,
                open_mode="wb")
        else:
            exp_sett = ExportSettings()
        return exp_sett

    def _is_export_path_exist(self):
        """
        Возвращает результат проверки существования или, при необходимости,
        создания пути экспорта"""
        try:
            self._exp_file_path.resolve().parent.mkdir(parents=True, exist_ok=True)
        except Exception as ex:
            logger.error(f"Ошибка при проверке пути экспорта. {ex}")
            return False
        else:
            return True

    def _is_export_possible(self, processed_data) -> bool:
        """Возвращает возможность экспорта"""
        if not self._format.supported:
            logger.error(f"Не поддерживается выгрузка данных в формат '{self._format.format}'")
            return False
        if processed_data is None:
            logger.error(f"Нет данных для экспорта в формат '{self._format.format}'")
            return False
        if not self._is_export_path_exist():
            return False
        return self._custom_checking_processed_data(processed_data)

    def _to_file(self, file_data) -> str | None:
        """
        Экспортирует daнные в файл экспорта.

        Results
        ---
        - str | None - название файла
        """
        try:
            with open(
                    self._exp_file_path, self._format.open_mode,
                    encoding=self._format.encoding, newline=self._format.newline) as f:
                f.write(file_data)
        except Exception:
            logger.exception(f"Не удалось сохранить файл экспорта '{self._exp_file_path}'")
            return None
        else:
            return self._exp_file_path.name
