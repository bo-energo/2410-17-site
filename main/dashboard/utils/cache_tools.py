import logging

from django.core.cache import caches
from django.http import JsonResponse


logger = logging.getLogger(__name__)


def get_cache_key(
        args: tuple,
        kwargs: dict,
        args_for_cache_key: list[int] = None,
        kwargs_for_cache_key: list[str] = None):
    """
    Получить ключ для кеша.

    Parameters:
    ---
    - args - кортеж позиционных аргументов;
    - kwargs - словарь именованных аргументов;
    - args_for_cache_key - список индексов позиционных аргументов используемых
    для формирования ключа кеша;
    - kwargs_for_cache_key -  список ключей именованных аргументов используемых
    для формирования ключа кеша.
    """
    try:
        if args_for_cache_key:
            key_from_args = [args[i] for i in sorted(args_for_cache_key)]
        else:
            key_from_args = "any_args"
        if kwargs_for_cache_key:
            key_from_kwargs = {i: kwargs.get(i) for i in sorted(kwargs_for_cache_key)}
        else:
            key_from_kwargs = "any_kwargs"
        return f"{str(key_from_args)}, {str(key_from_kwargs)}"
    except Exception as ex:
        logger.error(f"Не удалось создать ключ кеша. {ex}")
        return None


def success_json_response_cache(cache: str,
                                timeout: int = None,
                                args_for_cache_key: list[int] = None,
                                kwargs_for_cache_key: list[str] = None):
    """
    Декоратор кеширования успешного результата выполнения функций
    возвращающих результат типа JsonResponse.
    """
    def decorator(func: object):
        def wrapper(*args, **kwargs):
            cache_key = get_cache_key(args, kwargs, args_for_cache_key, kwargs_for_cache_key)
            if (res := caches[cache].get(cache_key)):
                return res
            res = func(*args, **kwargs)
            if isinstance(res, JsonResponse) and res.status_code == 200 and cache_key:
                caches[cache].set(cache_key, res, timeout)
            return res
        return wrapper
    return decorator
