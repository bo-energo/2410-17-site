import logging
import psycopg2
from psycopg2.extras import execute_values
from typing import Dict

from main.settings import DATABASES


logger = logging.getLogger(__name__)


class SqlManager:
    __db_settings: Dict[str, Dict[str, str]] = DATABASES

    def __init__(self, use_base: str = "default"):
        settings = self.__db_settings.get(use_base)
        if isinstance(settings, dict):
            try:
                self.__dbname = settings.get("NAME")
                self.__user = settings.get("USER")
                self.__password = settings.get("PASSWORD")
                self.__host = settings.get("HOST")
                self.__port = settings.get("PORT")
            except Exception:
                raise ValueError(f"Для базы {use_base} отсутствует значение "
                                 f"для одного из ключей [NAME, USER, PASSWORD, HOST, PORT]")
        else:
            raise ValueError("Настройки соединения ожидаются в dict")

    def execute(self, sql: str, argslist: list = None):
        try:
            with psycopg2.connect(dbname=self.__dbname, user=self.__user,
                                  password=self.__password, host=self.__host,
                                  port=self.__port) as conn:
                with conn.cursor() as cursor:
                    if argslist:
                        return execute_values(cursor, sql, argslist)
                    else:
                        cursor.execute(sql)
                        return cursor.fetchall()
        except Exception:
            logger.exception(f"Не выполнен запрос.\nSQL:{sql}\n Аргументы:{argslist}")
            return None
