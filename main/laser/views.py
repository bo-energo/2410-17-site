from django.http import JsonResponse

from laser import use_cases


def online(request) -> object:
    """Получить ip подключенного прибора Laser"""
    result, req_status = use_cases.online()

    result["status"] = req_status.get_message()
    return JsonResponse(
        result,
        json_dumps_params={'ensure_ascii': False},
        status=req_status.get_number_status()
    )


def read_data(request) -> object:
    """Прочитать данные с прибора Laser"""
    get = request.GET
    result, req_status = use_cases.read_data(
        date_start=get.get("dateStart"),
        date_end=get.get("dateEnd"),
        asset_guid=get.get("asset"),
        ip=get.get("ip"))

    result["status"] = req_status.get_message()
    return JsonResponse(
        result,
        json_dumps_params={'ensure_ascii': False},
        status=req_status.get_number_status()
    )


def get_all_loaded_data_info(request) -> object:
    """Получить данные о всех загрузках измерений"""
    result, req_status = use_cases.get_all_loaded_data_info()

    result["status"] = req_status.get_message()
    return JsonResponse(
        result,
        json_dumps_params={'ensure_ascii': False},
        status=req_status.get_number_status()
    )


def get_loaded_data_info(request) -> object:
    """Получить данные об одной загрузке измерений"""
    get = request.GET
    result, req_status = use_cases.get_loaded_data_info(id=get.get("id"))

    result["status"] = req_status.get_message()
    return JsonResponse(
        result,
        json_dumps_params={'ensure_ascii': False},
        status=req_status.get_number_status()
    )


def check_diag_settings(request) -> object:
    get = request.GET
    result, req_status = use_cases.check_diag_settings(get.get("asset"))

    result["status"] = req_status.get_message()
    return JsonResponse(
        result,
        json_dumps_params={'ensure_ascii': False},
        status=req_status.get_number_status()
    )
