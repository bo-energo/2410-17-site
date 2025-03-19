import logging
import hashlib
import pickle

from copy import deepcopy

from dashboard.models import ResultHashes


logger = logging.getLogger(__name__)


def hash_result_with_status(
        input_hash_name: str = "input_hash",
        output_hash_name: str = "hash",
        db_tables: tuple[str] = None):
    """
    Декоратор добавления в результат, полученный в виде (result: dict, status),
    хеша result.
    """
    def decorator(func: object):
        def wrapper(*args, **kwargs):
            input_hash = kwargs.pop(input_hash_name, None)

            func_path = f"{getattr(func, '__module__', '')}.{getattr(func, '__name__', '')}"
            hash_args = deepcopy(kwargs)
            hash_args["args"] = args
            output_hash = get_hash_from_db(func_path, hash_args)

            if output_hash is not None and input_hash == output_hash:
                result = {}
                status = True
            else:
                results = func(*args, **kwargs)
                try:
                    result, status = results
                    if not isinstance(result, dict):
                        raise ValueError(f"Ожидается result типа 'dict', получен - {type(result)}")
                    if not isinstance(status, bool):
                        raise ValueError(f"Ожидается status типа 'bool', получен - {type(status)}")
                    if status is not True:
                        raise ValueError("Ожидается 'status' = False")
                except Exception as ex:
                    logger.error(f"Ошибка разбора результатов функции {func_path}. {ex}")
                    return results
                else:
                    tables = " ".join(db_tables)
                    output_hash = save_hash_from_db(tables, func_path, hash_args, result)

            result[output_hash_name] = output_hash
            return result, status
        return wrapper
    return decorator


def get_hash(obj: any, hash_name: str = "sha1"):
    if not (b_obj := get_bytes(obj)):
        return None
    try:
        hsh = getattr(hashlib, hash_name)()
    except Exception as ex:
        logger.error(f"Ошибка создания хеш-объекта. {ex}")
        return None
    hsh.update(b_obj)
    return hsh.hexdigest()


def get_bytes(obj: any):
    try:
        return pickle.dumps(obj)
    except Exception as ex:
        logger.error(f"Ошибка сериализации объекта. {ex}")
        return None


def get_hash_from_db(func_name: str, input_args: dict):
    if not (b_input_args := get_bytes(input_args)):
        return None
    try:
        res_hsh = ResultHashes.objects.get(func=func_name, input_args=b_input_args)
    except Exception as ex:
        logger.error(f"Не удалось найти запись в ResultHashes. {ex}")
        return None
    else:
        return res_hsh.hash


def save_hash_from_db(db_tables: str, func_name: str, input_args: dict, result: any):
    if not (b_input_args := get_bytes(input_args)):
        return None
    if not (hash := get_hash(result)):
        return None
    try:
        ResultHashes.objects.update_or_create(
            defaults={"hash": hash}, tables=db_tables, func=func_name, input_args=b_input_args)
    except Exception as ex:
        logger.error(f"Не удалось сохранить запись в ResultHashes. {ex}")
        return None
    else:
        return hash


def get_or_save_hash_from_db(db_tables: str, func_name: str, input_args: dict, result: any):
    hash = get_hash_from_db(func_name, input_args)
    if hash is None:
        hash = save_hash_from_db(db_tables, func_name, input_args, result)
    return hash


def clear_hash_in_db(db_table: str):
    hashes = ResultHashes.objects.filter(tables__icontains=db_table)
    for hsh in hashes:
        hsh.hash = None
    ResultHashes.objects.bulk_update(hashes, ["hash"])
