import logging
from django.db import transaction
from config_ui.models import models, PagePanelLocation, PageBlockLocation, UiSettings


logger = logging.getLogger(__name__)


def get_ui_settings():
    """Возвращает настройки пользовательского интерфейса"""
    ui_settings = UiSettings.objects.all()
    result = {}
    status = True
    for rec in ui_settings:
        if rec.value_type == "int":
            try:
                rec.value = int(rec.value)
            except Exception:
                message = (
                    f"Для параметра настроек поль. интерфейса {rec.code} "
                    f"не удалось преобразовать значение {rec.value} в целое число")
                logger.error(message)
                status = status and False
                continue
        elif rec.value_type == "float":
            try:
                rec.value = float(rec.value)
            except Exception:
                message = (
                    f"Для параметра настроек поль. интерфейса {rec.code} "
                    f"не удалось преобразовать значение {rec.value} в вещественное число")
                logger.error(message)
                status = status and False
                continue
        result[rec.code] = rec.value
    return result, status


def update_locations(input_panel_locs: list[dict], input_page_locs: list[dict]):
    """Сохраняет полученные настройки расположения панелей и блоков"""
    panel_locs = _get_updating_locations(PagePanelLocation, input_panel_locs)
    page_locs = _get_updating_locations(PageBlockLocation, input_page_locs)
    try:
        with transaction.atomic():
            count_p = PagePanelLocation.objects.bulk_update(
                panel_locs, ["x", "y", "w", "h", "min_w", "min_h"])
            count_b = PageBlockLocation.objects.bulk_update(
                page_locs, ["x", "y", "w", "h", "min_w", "min_h"])
        logger.info(
            f"Для {count_p} панелей  и {count_b} блоков UI обновлены позиции.")
    except Exception as ex:
        logger.error(f"Не удалось сохранить позиции панелей и блоков UI. {ex}")
        return False
    else:
        return True


def _get_updating_locations(model: models, input_locs: list[dict]):
    """Возвращает обновленные расположения визуальных элементов"""
    input_locs = {int(info.get("i")): info for info in input_locs}
    locs = model.objects.filter(id__in=list(input_locs.keys())).only("id", "x", "y", "w", "h")
    for loc in locs:
        info = input_locs.get(loc.id, {})
        loc.x = info.get("x", loc.x)
        loc.y = info.get("y", loc.y)
        loc.w = info.get("w", loc.w)
        loc.h = info.get("h", loc.h)
        loc.min_w = info.get("min_w", loc.min_w)
        loc.min_h = info.get("min_h", loc.min_h)
    return locs
