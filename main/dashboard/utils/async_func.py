import asyncio
from typing import Callable, Iterable, TypeAlias


DBQueryFunc: TypeAlias = Callable[..., tuple[Iterable, bool]]


async def get_queries_results(func: DBQueryFunc, queries_params: list[dict]):
    """
    Возвращает список результатов выполнения асинхронной функции запроса к базе данных

    Parametrs:
    ---
    - func - асинхронная функция которая будет использоваться для запроса данных
    - queries_params - список наборов аргументов для вызова 'func'

    Return:
    ---
    - (список результатов выполнения 'func', совокупный статус всех попыток выполнения 'func')
    """
    queries_results = await asyncio.gather(
        *(func(**params) for params in queries_params))
    status = True
    result = []
    for meterings, res_status in queries_results:
        result.append(meterings)
        status = status and res_status
    return result, status
