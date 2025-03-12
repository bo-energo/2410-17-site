import logging
import tablib
from typing import Dict, Any

from dashboard.utils import to_pdf
from dashboard.services.export.export_manager import ExportManager


logger = logger = logging.getLogger(__name__)


class SgnValuesExpManager(ExportManager):
    """Менеджер экспорта в файл значений сигналов"""

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
        return "signal_values"

    def _get_data_for_write_to_file(self, processed_data: tablib.Dataset) -> Any | None:
        """Возвращает файловые данные для записи"""
        try:
            if self._format == "pdf":
                buffer = to_pdf.create_signal_value_file(
                    processed_data, self._exp_file_path.name)
            else:
                buffer = processed_data.export(self._format, **self._format.kwargs)
        except Exception as ex:
            logger.error(f"Ошибка формирования данных для записи в файл экспорта. {ex}")
            buffer = None
        return buffer

    def _get_processed_data(self, input_data: Dict[str, Dict[str, Any]]):
        """Создает датасет для экспорта"""
        dataset = tablib.Dataset()
        headers = input_data.pop("headers", None)
        if isinstance(headers, list):
            dataset.headers = ["Время", *headers]
            for time, values in input_data.items():
                row = [time]
                row.extend(values.get(named) for named in headers)
                dataset.append(row)
            dataset = dataset.sort(0)
        return dataset

    def _update_format_settings(self):
        """Обновляет объект конфигурации экспорта"""
        if self._format.format not in {"html", "csv", "xls", "pdf"}:
            self._format.supported = False
