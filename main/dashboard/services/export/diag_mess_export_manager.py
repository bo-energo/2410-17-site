import logging
import tablib
from typing import List, Dict, Any, Union

from dashboard.utils import to_pdf
from dashboard.services.export.export_manager import ExportManager


logger = logger = logging.getLogger(__name__)


class DiagMessExpManager(ExportManager):
    """Менеджер экспорта в файл диагностических сообщений"""

    def __init__(self, format, name_exp_file):
        super().__init__(format, name_exp_file)

    def _custom_checking_processed_data(self, processed_data) -> bool:
        """Возвращает корректность обработанных данных для экспорта"""
        if isinstance(processed_data, tablib.Dataset):
            return True
        else:
            logger.error(
                "Данные после обработки ожидаются типа 'tablib.Dataset', "
                f"получены типа '{type(processed_data)}'")
            return False

    def _default_file_name(cls):
        """Возвращает имя файла экспорта по умолчанию"""
        return "diag_mess"

    def _get_data_for_write_to_file(self, processed_data: tablib.Dataset) -> Any | None:
        """Возвращает файловые данные для записи"""
        try:
            if self._format.format == "pdf":
                buffer = to_pdf.create_diag_message_file(processed_data, self._exp_file_path.name)
            else:
                buffer = processed_data.export(self._format.format, **self._format.kwargs)
        except Exception as ex:
            logger.error(f"Ошибка формирования данных для записи в файл экспорта. {ex}")
            buffer = None
        return buffer

    def _get_processed_data(self, input_data: Dict[str, Union[List[str], List[Dict[str, Any]]]]):
        """Создает датасет для экспорта"""
        dataset = tablib.Dataset()
        headers = input_data.pop("headers", None)
        if isinstance(headers, list):
            dataset.headers = headers
            values = input_data.get("data")
            if values and isinstance(values, list):
                for record in values:
                    row = [record.get(named) for named in headers]
                    dataset.append(row)
            dataset = dataset.sort(0)
        return dataset

    def _update_format_settings(self):
        """Обновляет объект конфигурации экспорта"""
        if self._format.format not in {"html", "csv", "xls", "pdf"}:
            self._format.supported = False
