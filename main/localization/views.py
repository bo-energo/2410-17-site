import logging
from django.http import JsonResponse

from dashboard.utils import time_func, request_status
from .services.translation import use_cases as translt_use_cases


logger = logging.getLogger(__name__)


def get_langs(request) -> object:
    """Возвращает список доступных языков"""
    req_status = request_status.RequestStatus(True)
    result = translt_use_cases.get_all_langs()

    result["status"] = req_status.get_message()
    return JsonResponse(
        result,
        json_dumps_params={'ensure_ascii': False},
        status=req_status.get_number_status()
    )


@time_func.runtime_in_log
def get_translated_interface(request, lng: str) -> object:
    """Возвращает элементы интерфейса переведенные на запрашиваемый язык"""
    req_status = request_status.RequestStatus(True)
    result, status = translt_use_cases.get_interface_all_translts(lng)

    req_status.add(status, f"Нет словаря для языка {lng}")
    result["status"] = req_status.get_message()
    return JsonResponse(
        result,
        json_dumps_params={'ensure_ascii': False},
        status=req_status.get_number_status()
    )
