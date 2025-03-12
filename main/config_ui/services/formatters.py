import logging

from datetime import date


logger = logging.getLogger(__name__)


def to_duval_triangle(template: dict[str, list[list[str]]]):
    """Возвращает отформатированные данные для шаблона треугольника Дюваля"""
    if not template or not isinstance(template, dict):
        return template
    input_keys = list(template.keys())
    result = {"dates": []}
    result.update({key: [] for key in input_keys})
    # проходим по данным для первого ключа из шаблона
    # и формируем словарь данных разнесенных по времени
    times_data: dict[str, dict[str, str]] = {}
    first_key = input_keys[0]
    try:
        for time, value in template.get(first_key, []):
            times_data[time] = {first_key: value}
        # проходим по оставшимся ключам из шаблона
        # и дополняем словарь данных разнесенных по времени
        for key in input_keys[1:]:
            for time, value in template.get(key):
                # добавляем данные, если момент времени time уже есть
                # в словаре данных разнесенных по времени
                if time not in times_data:
                    continue
                times_data[time][key] = value
        for t, _ in template.get(first_key, []):
            t_data = times_data.get(t, {})
            # если кол-во ключей в данных для момента времени t не совпадает
            # c кол-вом ключей шаблона то данные в результат не добавляем
            if len(t_data.keys()) != len(input_keys):
                continue
            result["dates"].append(t)
            for key in input_keys:
                result[key].append(t_data.get(key))
    except Exception as ex:
        logger.error(f"Ошибка при форматировании шаблона виджета треугольника Дюваля. {ex}")
    template.update(result)
    return template


def to_duval_pentagon(template: dict[str, list[list[str]]]):
    """Возвращает отформатированные данные для шаблона треугольника Дюваля"""
    if not template or not isinstance(template, dict):
        return template
    input_keys = list(template.keys())
    result = {"dates": []}
    result.update({key: [] for key in input_keys})
    # проходим по данным для первого ключа из шаблона
    # и формируем словарь данных разнесенных по времени
    times_data: dict[str, dict[str, str]] = {}
    first_key = input_keys[0]
    try:
        for time, value in template.get(first_key, []):
            times_data[time] = {first_key: value}
        # проходим по оставшимся ключам из шаблона
        # и дополняем словарь данных разнесенных по времени
        for key in input_keys[1:]:
            for time, value in template.get(key):
                # добавляем данные, если момент времени time уже есть
                # в словаре данных разнесенных по времени
                if time not in times_data:
                    continue
                times_data[time][key] = value
        for t, _ in template.get(first_key, []):
            t_data = times_data.get(t, {})
            # если кол-во ключей в данных для момента времени t не совпадает
            # c кол-вом ключей шаблона то данные в результат не добавляем
            if len(t_data.keys()) != len(input_keys):
                continue
            result["dates"].append(t)
            for key in input_keys:
                result[key].append(t_data.get(key))
    except Exception as ex:
        logger.error(f"Ошибка при форматировании шаблона виджета треугольника Дюваля. {ex}")
    template.update(result)
    return template


def to_box_chart(template: list[list[str]]):
    """Возвращает отформатированные данные для шаблона ящика с усами"""
    if not template or not isinstance(template, list):
        return template
    date_format = "%Y.%m.%d"
    result = []
    try:
        daily_data = {}
        for t, value in template:
            daily_data_date = daily_data.get("timestamp")
            try:
                t_date = t.date()
            except Exception as e:
                logger.error(f"Ошибка преобразования метки времени {t} к объекту datetime. {e}")
                continue
            if daily_data_date != t_date:
                if daily_data_date and daily_data.get("values"):
                    daily_data["timestamp"] = date.strftime(daily_data_date, date_format)
                    result.append(daily_data)
                daily_data = {"timestamp": t_date, "values": []}
            daily_data["values"].append(value)
    except Exception as ex:
        logger.error(f"Ошибка при форматировании шаблона виджета ящика с усами. {ex}")
    return result


def to_text_field(template: list[str], signals: dict):
    """Возвращает отформатированные данные для шаблона текстового поля"""
    result = []
    for s in template:
        try:
            s = s.format(**signals)
        except Exception as ex:
            logger.error(f"Ошибка при форматировании строк шаблона виджета текстового поля. {ex}")
        result.append(s)
    return result
