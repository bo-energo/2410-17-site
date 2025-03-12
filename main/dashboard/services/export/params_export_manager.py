import logging
from typing import List, Dict, Any, Union

from dashboard.utils import to_pdf
from dashboard.services.export.export_manager import ExportManager, ExportSettings


logger = logger = logging.getLogger(__name__)


class ParamsExportManager(ExportManager):
    """Менеджер экспорта в файл значений параметров"""

    def __init__(self, format, name_exp_file):
        super().__init__(format, name_exp_file)

    def _custom_checking_processed_data(self, processed_data) -> bool:
        """Возвращает корректность обработанных данных для экспорта"""
        if isinstance(processed_data, dict):
            return True
        else:
            logger.error(
                "Данные после обработки ожидаются типа 'dict', "
                f"получены типа '{type(processed_data)}'")
            return False

    def _default_file_name(cls):
        """Возвращает имя файла экспорта по умолчанию"""
        return "params"

    def _get_data_for_write_to_file(self, processed_data: dict) -> Any | None:
        """Возвращает файловые данные для записи"""
        try:
            buffer = to_pdf.create_diag_config_data_file(processed_data, self._exp_file_path.name)
        except Exception as ex:
            logger.error(f"Ошибка формирования данных для записи в файл экспорта. {ex}")
            buffer = None
        return buffer

    def _get_processed_data(self, input_data: Dict[str, Union[List[str], List[Dict[str, Any]]]]):
        """Создает датасет для экспорта"""
        return input_data

    def _update_format_settings(self):
        """Обновляет объект конфигурации экспорта"""
        if not self._format.format:
            self._format = ExportSettings("pdf", True, open_mode="wb")
        if self._format.format not in {"pdf"}:
            self._format.supported = False
