import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt


from dashboard.utils import request_status

from config_ui.services import use_cases


logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def update_blocks_info(request) -> object:
    req_status = request_status.RequestStatus(True)
    body = json.loads(request.body)
    result = use_cases.update_locations(body.get("outter", []), body.get("inner", []))
    req_status.add(result, "Не удалось обновить позиции блоков UI.")
    json_resp = {
            "status": req_status.get_message()
        }
    return JsonResponse(
        json_resp,
        json_dumps_params={'ensure_ascii': False},
        status=req_status.get_number_status()
    )


def ui_settings(request) -> object:
    req_status = request_status.RequestStatus(True)
    result, status = use_cases.get_ui_settings()
    req_status.add(status, "Возникли ошибки при получении настроек")
    result["status"] = req_status.get_message()
    return JsonResponse(
        result,
        json_dumps_params={'ensure_ascii': False},
        status=req_status.get_number_status()
    )
