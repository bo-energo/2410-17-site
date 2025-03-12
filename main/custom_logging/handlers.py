from logging import Formatter
from logging.handlers import QueueListener, RotatingFileHandler


class CustQueueListener(QueueListener):
    def __init__(self, cust_level, queue, handlers, respect_handler_level: bool = False):
        super().__init__(queue, *handlers, respect_handler_level=respect_handler_level)
        self.level = cust_level


class CustFileHandler:
    def __init__(self, full_filename: str, maxBytes: int, backupCount: int, file_fmt: str):
        self.__formatter = Formatter(file_fmt)
        self.__handler = RotatingFileHandler(
            filename=full_filename,
            maxBytes=maxBytes,
            backupCount=backupCount,
            encoding='UTF8'
        )
        self.__handler.setFormatter(self.__formatter)

    def get_handler(self):
        return self.__handler
