import logging
from typing import Tuple
from datetime import datetime, timedelta, timezone
from time import perf_counter
from zoneinfo import ZoneInfo

from main.settings import TIME_ZONE


logger = logging.getLogger(__name__)


def runtime_in_log(func: object):
    """Декоратор записи в лог времени выполнения функции"""
    def wrapper(*args, **kwargs):
        start = perf_counter()
        res = func(*args, **kwargs)
        logger.info(f"--- RUNTIME of the {func.__module__}.{func.__qualname__} = "
                    f"{(perf_counter() - start):.05f}")
        return res
    return wrapper


@runtime_in_log
def define_date_interval(
        date_start: datetime | str | None,
        date_end: datetime | str | None) -> Tuple[datetime, datetime]:
    """
    Определяет интервал дат.
    Возвращаются в порядке: date_start, date_end.
    """
    def specific_replace(dt: datetime):
        try:
            return dt.replace(microsecond=0)
        except Exception:
            return None

    logger.info(f"{date_start = }  {date_end = }")

    date_start, date_end = (
        specific_replace(normalize_date(date))
        for date in (date_start, date_end)
    )
    datenow = specific_replace(datetime.now(tz=get_tz()))
    # 1 случай. Нет обоих дат.
    # Определяется интервал
    # от (datenow - 7 суток) до datenow,
    if not date_start and not date_end:
        date_end = datenow
        date_start = date_end - timedelta(days=7)
    # 2 случай. Нет даты начала, есть дата окончания.
    # Определяется интервал
    # от (date_end - 7 суток) до date_end,
    elif not date_start and date_end:
        date_start = date_end - timedelta(days=7)
    # 3 случай. Есть дата начала, нет даты окончания.
    # определяется интервал от date_start до datenow
    elif date_start and not date_end:
        date_end = datenow
    # Даты меняются если date_start > date_end
    if date_end < date_start:
        date_start, date_end = date_end, date_start
    logger.info(f"Definite interval dates: {date_start}  -  {date_end}")
    return date_start, date_end


def fix_string_datetime_format(date_string: str):
    """
    Исправляет формат строки времени для последующей конвертации.
    Если в конце 'date_string' есть символ 'z', то он заменяется на '+00:00'
    и возвращается строковое представление момента времени осведомленного о
    смещении часового пояса.
    """
    if isinstance(date_string, str) and len(date_string) and date_string[-1].lower() == 'z':
        return f"{date_string[:-1]}+00:00"
    else:
        return date_string


def get_tz(timezone: str = TIME_ZONE):
    """
    Возвращает ZoneInfo для 'timezone'. При ошибке
    создания ZoneInfo для 'timezone',возвращает
    ZoneInfo часового пояса сервера Django
    """
    try:
        return ZoneInfo(timezone)
    except Exception:
        return ZoneInfo(TIME_ZONE)


def safe_str_to_date(date_string: str, format: str = None):
    """
    Конвертирует строку времени в datetime.
    При неудачной конвертации возвращает None.
    """
    date_string = fix_string_datetime_format(date_string)
    if format:
        try:
            date = datetime.strptime(date_string, format)
        except Exception:
            date = None
            logger.error(f"Не удалось конвертировать строку='{date_string}' в дату согласно формату {format}")
    else:
        try:
            date = datetime.fromisoformat(date_string)
        except Exception:
            date = None
            logger.error(f"Не удалось конвертировать строку='{date_string}' в дату согласно ISO форматам")
    return date


def safe_astimezone(dt: datetime | None, timezone: str = TIME_ZONE):
    """
    Возвращает объект datetime соответсвующий 'dt' в часовом поясе 'timezone'.
    Если 'timezone' некорректно то используется часовой пояс сервера Django.
    Если 'dt' является неосведомленным о часовом поясе,
    то считается что 'dt' указано в часовом поясе сервера Django.
    Если 'dt' не является datetime, возвращает None.
    """
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo(TIME_ZONE))
        return dt.astimezone(get_tz(timezone))
    else:
        return None


def normalize_date(dt: datetime | str | None, timezone: str = TIME_ZONE, format: str = None):
    """
    Возвращает объект datetime соответсвующий 'dt' в часовом поясе timezone.
    Если 'timezone' некорректно, то используется часовой пояс сервера Django.
    Если 'dt' является неосведомленным о часовом поясе,
    то считается что 'dt' указано в часовом поясе сервера Django.
    При неудачной конвертации возвращает None.
    """
    if isinstance(dt, str):
        dt = safe_str_to_date(dt, format)
    return safe_astimezone(dt, timezone)


def now_with_tz(timezone: str = TIME_ZONE) -> datetime:
    """
    Возвращает текущий момент времени. Если timezone корректный,
    то в в часовом поясе timezone, иначе в часовом поясе сервера Django
    """
    try:
        return datetime.now(ZoneInfo(timezone))
    except Exception:
        return datetime.now(ZoneInfo(TIME_ZONE))


DATE_FORMAT_STR: str = "%Y-%m-%dT%H:%M:%S.%fZ"  # 2024-11-14T14:30:13.000Z


def datestr_to_timestamp(
    datestr: str,
    dt_format: str = DATE_FORMAT_STR,
) -> int:
    """Преобразует строку даты и времени в метку времени timestamp"""

    return int(
        datetime.strptime(datestr, dt_format)
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )


def timestamp_to_server_datestr(
    timestamp: int | float,
    tz: ZoneInfo | None = None,
    dt_format: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """Преобразует метку времени timestamp в строку даты и времени."""

    if tz is None:
        tz = get_tz()

    return datetime.fromtimestamp(timestamp, tz).strftime(dt_format)
