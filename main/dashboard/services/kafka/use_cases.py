import logging
from typing import List, Iterable, Union

from main.settings import KAFKA, TOPICS
from dashboard.models import Assets, Devices, SignalsGuide
from dashboard.utils.kafka_drv import KafkaProd
from dashboard.utils import guid
from dashboard.services.mms.mms_config import MMSConfig
from django.contrib import messages


logger = logging.getLogger(__name__)


def send_devices(modified_entity: str = ""):
    """Отправка сигналов в разрезе приборов в Kafka"""
    devices = Devices.changes_for_kafka()
    try:
        return KafkaProd.send_devices_to_kafka(*devices)
    except Exception:
        logger.exception(f"ERROR when sending {modified_entity} changes to Kafka.")
        return False, ["Не удалось отправить настройки сигналов в Kafka"]


def send_assets(model_admin, request):
    """Отправка оборудований в Kafka"""

    assets = Assets.get_for_kafka()
    topic = TOPICS.get("ASSETS")
    status: bool = KafkaProd.send_assets(topic, assets)
    if status:
        model_admin.message_user(
            request,
            "Данные оборудований отправлены в Kafka",
            messages.SUCCESS,
        )
    else:
        model_admin.message_user(
            request,
            f"Ошибка отправки данных оборудований в Kafka (топик '{topic}')! "
            f"Проверьте, что Kafka запущена и работает. "
            f"Проверьте корректность адреса подключения: '{KAFKA}'",
            messages.ERROR,
        )


def _send_sg_guide(sg_guide: Union[dict, List[dict]]):
    """Отправка signal_guide в Kafka"""
    topic = KafkaProd.get_topic_name("TOPIC_FOR_SIGNALS_GUIDE")
    result_check = KafkaProd.get_check_settings_result(KAFKA, topic)
    if result_check:
        logger.error("Incorrect settings of environment variables for sending data to Kafka: "
                     f"Server KAFKA = {KAFKA}, TOPIC_FOR_SIGNALS_GUIDE = {topic}.")
        return False, result_check
    if not sg_guide:
        logger.error(f"Empty value to send to the Kafka topic '{topic}'.")
        return False, "Нет данных для отправки в Kafka."
    try:
        KafkaProd.default_producer().send(
            topic=topic,
            value=sg_guide, key=guid.generate()
        )
        return True, "Настройки кодов сигналов успешно отправлены в Kafka."
    except Exception:
        logger.exception(f"ERROR when sending SignalsGuide to the Kafka topic '{topic}'.")
        return False, "Не удалось отправить настройки кодов сигналов в Kafka."


def send_list_sg_guide(sg_guides: Iterable[SignalsGuide] = None):
    """
    Отправка списка SignalsGuide в Kafka. Если sg_guides None или пуст,
    то отправляются все SignalsGuide."""
    if not sg_guides:
        sg_guides = SignalsGuide.objects.all()
    if isinstance(sg_guides, Iterable):
        try:
            value = [sg.get_for_kafka() for sg in sg_guides]
        except Exception:
            logger.exception("The dictionary of parameter values of the "
                             "'sg_guides' elements could not be obtained.")
            return False, "Не удалось сформировать данные для отправки."
    else:
        logger.exception("For sg_guides to be sent to Kafka, "
                         "the type 'Iterable' is expected, "
                         f"a {type(sg_guides)} is received.")
        return False, "Некорректный тип данных для отправки. Ожидается список кодов сигналов."
    return _send_sg_guide(value)


def send_sg_guide(sg_guide: SignalsGuide = None):
    """Отправка SignalsGuide в Kafka."""
    if isinstance(sg_guide, SignalsGuide):
        value = sg_guide.get_for_kafka()
    else:
        logger.exception("For sg_guide to be sent to Kafka, "
                         "the type 'SignalsGuide' is expected, "
                         f"a {type(sg_guide)} is received.")
        return False, "Данные для отправки в Kafka не являются кодом сигнала."
    return _send_sg_guide(value)


def send_mms_config():
    data = MMSConfig.get_data()
    topic = TOPICS.get("MMS_CONFIG")
    result_check = KafkaProd.get_check_settings_result(KAFKA, topic)
    if result_check:
        logger.error("Incorrect settings of environment variables for sending data to Kafka.")
        return False, result_check
    try:
        KafkaProd(bootstrap_servers=KAFKA).send(topic=TOPICS.get("MMS_CONFIG"),
                                                value=data,
                                                key=guid.generate())
    except Exception:
        logger.exception("Failed to send data for MMS server to"
                         " Kafka 'MMS_CONFIG' topics")
        return False, "Не удалось отправить данные для MMS сервера в Kafka"
    else:
        return True, "Данные для MMS сервера успешно отправлены в Kafka"
