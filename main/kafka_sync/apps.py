import logging
import os
import sys
import time
from threading import Thread

from django.apps import AppConfig

from dashboard.services.kafka.utils import get_latest_topic_value
from dashboard.utils.kafka_drv import KafkaProd
from main.settings import KAFKA, TOPICS


logger_kafka_conn = logging.getLogger("kafka.conn")
logger_kafka_conn.setLevel(logging.WARNING)
logger_kafka_coordinator = logging.getLogger("kafka.coordinator")
logger_kafka_coordinator.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def compare_and_update_assets():
    # импортируем внутри функции, так как использование моделей до инициализации приложения не разрешено
    from dashboard.models import Assets

    # получаем последние данные из Kafka
    latest_kafka_assets = get_latest_topic_value(topic=TOPICS.get("ASSETS"))

    # получаем последние данные из БД
    db_assets: list[dict] | None = Assets.get_for_kafka()

    # Если содержимое БД и Kafka не совпадает - обновляем содержимое в Kafka
    if db_assets is not None and latest_kafka_assets != db_assets:
        status = KafkaProd(bootstrap_servers=KAFKA).send_assets(TOPICS.get("ASSETS"), db_assets)
        if status:
            logger.info("Assets were updated in Kafka")


SYNCHRONIZE_FUNCTIONS = (
    compare_and_update_assets,
)


def sync_data_in_kafka_wrapper():
    while True:
        for sync_functon in SYNCHRONIZE_FUNCTIONS:
            function_name = sync_functon.__name__
            try:
                sync_functon()
            except Exception as e:
                logger.error(f"{e}. Error in sync function: {function_name}()")
        time.sleep(60)


class KafkaSyncConfig(AppConfig):
    name = "kafka_sync"
    verbose_name = "Kafka Sync"

    def __init__(self, app_name, app_module):
        super().__init__(app_name, app_module)

    def ready(self) -> None:
        if not self._is_runserver_or_asgi():
            return

        # https://stackoverflow.com/questions/33814615/how-to-avoid-appconfig-ready-method-running-twice-in-django
        if os.environ.get('RUN_MAIN'):
            sync_data_in_kafka_thread: Thread = Thread(
                target=sync_data_in_kafka_wrapper,
                name="sync_data_in_kafka_thread",
                daemon=True,
            )
            sync_data_in_kafka_thread.start()

    def _is_runserver_or_asgi(self):
        """Проверка, что текущая команда - runserver или ASGI"""
        return (
            len(sys.argv) > 1 and
            (sys.argv[1] == "runserver" or "daphne" in sys.argv[0] or "uvicorn" in sys.argv[0])
        )
