from typing import List, Union, Iterable


class RequestStatus:
    number_status = {True: 200, False: 405}

    def __init__(self, status: bool, err_message: List[str] | None = None):
        self.__status = status
        self.__err_message = []
        if not err_message:
            err_message = []
        if status is False:
            self.__add_err_message(err_message)

    def __add_err_message(self, err_message: Union[str, List[str]]):
        if isinstance(err_message, str):
            self.__err_message.append(err_message)
        elif isinstance(err_message, Iterable):
            self.__err_message.extend(err_message)

    def add(self, status: bool, err_message: Union[str, List[str]]):
        """Если статус False, то добавляет сообщение о причине"""
        self.__status = self.__status and status
        if status is False:
            self.__add_err_message(err_message)

    def get_number_status(self) -> int:
        """Получение числового статуса для HTTP ответа"""
        return self.number_status.get(self.__status)

    def get_status(self):
        """Получение статуса успешности подготовки ответа на запрос"""
        return self.__status

    def get_message(self):
        if self.__status:
            return ["Success",]
        else:
            return ["Error", self.__err_message]
