import logging
from typing import List, Tuple, Dict, Any

from .export_manager import ExportManager
from .diag_mess_export_manager import DiagMessExpManager
from .signal_values_export_manager import SgnValuesExpManager
from .params_export_manager import ParamsExportManager

logger = logger = logging.getLogger(__name__)


def data_to_file(params: dict, file_name: str,
                 data_type: str, data: Dict[str, Dict[str, Any]]) -> Tuple[List[str], bool]:
    """
    Сохраняет данные в файл.

    Arguments
    ---
    'data-type' - тип выгружаемых данных.
    Значение из списка ('signals', 'diag_messages', 'pdata', 'lim&const')
    """
    format, export_file_name = get_params(params, file_name)
    if data_type == 'diag_messages':
        return DiagMessExpManager(format, export_file_name).create_file(data)
    elif data_type == 'signals':
        return SgnValuesExpManager(format, export_file_name).create_file(data)
    elif data_type in {'pdata', "lim&const"}:
        return ParamsExportManager(format, export_file_name).create_file(data)


def get_response_file(input_params: dict):
    """Возвращает файл экспорта данных"""
    if not isinstance(report_name := input_params.get('name', ''), str):
        return None, False

    report_name = report_name.lower()
    report_name = "_".join(report_name.split(":"))

    return ExportManager.get_response_with_file(report_name)


def get_params(web_params: dict, export_file_name: str):
    """
    Возвращает словарь аргументов для формирования файла экспорта

    Results
    ---
    - ('формат файла экспорта', 'имя файла экспорта')
    """
    format = web_params.get("format")
    file_name = web_params.get("nameReport")
    if not file_name:
        file_name = export_file_name
    return format, file_name
