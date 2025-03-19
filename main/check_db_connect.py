from typing import TypeVar
from time import sleep
from psycopg2 import connect
from main.settings import URL_DB


ParseResult = TypeVar('ParseResult')


def check_db_connect(db_url: ParseResult = URL_DB):
    pause_len = 10  # sec
    while True:
        try:
            conn = connect(dbname=db_url.path[1:],
                           user=db_url.username,
                           password=db_url.password,
                           host=db_url.hostname,
                           port=db_url.port)
            conn.close()
            break
        except Exception as ex:
            print(ex)
            sleep(pause_len)
