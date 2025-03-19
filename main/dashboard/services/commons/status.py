def get_status_name(status):
    """Возвращает текстовое представление числового статуса"""
    try:
        status = abs(int(status))
    except Exception:
        status = None
    if status == 0:
        return "Good"
    elif status == 1:
        return "Warning"
    elif status == 2:
        return "Dangerous"
    else:
        return "Undefined"


def get_status_name_without_undefined(status):
    if (status := get_status_name(status)) == "Undefined":
        return "Good"
    else:
        return status


def diag_msg_status_eng_to_ru(status: str):
    """Возвращает уровень критичности диаг. сообщения на русском"""
    if status == "Good":
        return "Нормально"
    elif status == "Warning":
        return "Внимание"
    elif status == "Dangerous":
        return "Опасно"
    else:
        return ""


def txt_status_to_number100(status: str):
    """
    Возвращает статус конвертированный из текстового в числовой
    по шкале от 1 до 100.
    """
    if status == "Good":
        return 100
    elif status == "Warning":
        return 50
    elif status == "Dangerous":
        return 1
    else:
        return 100
