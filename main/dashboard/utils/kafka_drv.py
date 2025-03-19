import logging
import json
from typing import List
from kafka import KafkaProducer
from kafka.errors import KafkaError
from main.settings import KAFKA, TOPICS
from dashboard.utils import guid


logger = logging.getLogger(__name__)


class KafkaProd:
    """аргументы при создании:
    'topic': str - имя топика;\n
    'bootstrap_servers': list[str] - список ip:port брокеров
    """
    __instanse = None

    @classmethod
    def check_args(cls, servers):
        if not isinstance(servers, str):
            raise ValueError(f"Invalid value 'servers' = {servers} for creating Kafka producer")

    @classmethod
    def get_check_settings_result(cls, server: str, topic: str):
        messages = []
        for val_type, value in (("адрес сервера Каfka", server), ("топик Kafka", topic)):
            if not value:
                messages.append(f"Не задан {val_type}.")
            elif not isinstance(value, str):
                messages.append(f"{val_type.capitalize()} должен быть строкой.")
            elif all(s == " " for s in value):
                messages.append(f"Не задан {val_type}.")
        return " ".join(messages)

    @classmethod
    def send_devices_to_kafka(cls, readers, listeners):
        """Отправка списков приборов readers, listeners в Kafka"""
        messages: List[str] = []
        result = True
        for message in (KafkaProd.get_check_settings_result(KAFKA, TOPICS.get("READER")),
                        KafkaProd.get_check_settings_result(KAFKA, TOPICS.get("LISTENER"))):
            if message:
                result = False
                messages.append(message)
        if not result:
            return result, messages
        producer = cls(bootstrap_servers=KAFKA)
        if readers:
            producer.send(topic=TOPICS.get("READER"), value=readers,
                          key=guid.generate())
        if listeners:
            producer.send(topic=TOPICS.get("LISTENER"), value=listeners,
                          key=guid.generate())
        return result, ["Настройки сигналов успешно отправлены в Kafka"]

    @classmethod
    def send_signal_value(cls, topic: str, data: dict | list):
        """Отправка значения сигнала в Kafka"""
        if not isinstance(data, (dict, list)):
            return False
        try:
            send_kafka_result = cls(bootstrap_servers=KAFKA).send(topic, data, guid.generate())
        except Exception:
            send_kafka_result = False
            logger.exception(f"ERROR when sending data to Kafka topic '{topic}'.")
        return send_kafka_result

    @classmethod
    def send_assets(cls, topic: str, data: dict | list) -> bool:
        """Отправка данных оборудований в Kafka.

        Возвращает булев статус успешности отправки данных.
        """

        try:
            send_kafka_result = cls(bootstrap_servers=KAFKA).send(
                topic=topic,
                value=data,
                key=guid.generate(),
            )
        except Exception:
            send_kafka_result = False
            logger.exception(f"ERROR when sending assets to Kafka topic '{topic}'.")
        return send_kafka_result

    def __new__(cls, *args, **kwargs):
        servers = kwargs.get("bootstrap_servers")
        cls.check_args(servers)
        try:
            producer = KafkaProd.__instanse
            if isinstance(producer, cls):
                if producer.config().get('bootstrap_servers') == servers:
                    instance = producer
                else:
                    producer.close()
                    raise ValueError("The existing producer has a different IP")
            else:
                raise ValueError("The producer does not exist or incorrect")
        except Exception:
            logger.exception("")
            logger.info("A new producer will be created.")
            instance = super().__new__(KafkaProd)
        cls.__instanse = instance
        return instance

    def __init__(self, bootstrap_servers: list, **kwargs):
        try:
            self.producer = KafkaProducer(bootstrap_servers=bootstrap_servers,
                                          **kwargs)
        except Exception as ex:
            logger.exception(f"Failed to initialize producer. {bootstrap_servers = }")
            self.producer = None
            raise ex

    @classmethod
    def default_producer(cls):
        return cls(bootstrap_servers=KAFKA)

    @classmethod
    def get_topic_name(cls, key: str):
        return TOPICS.get(key)

    def config(self) -> dict:
        """Возвращает конфиг продюсера"""
        res = self.producer.config
        return res.copy()

    def send(self, topic, value, key, debug=True):
        """Отправка данных в брокер"""
        logger.info(f"\n{topic = }  {key = }\n{value = }")
        if isinstance(value, (list, dict)):
            value = bytes(json.dumps(value), encoding='utf-8')
        else:
            value = bytes(str(value), encoding='utf-8')
        if not isinstance(key, bytes):
            key = bytes(str(key), encoding='utf-8')
        future = self.producer.send(topic, value=value, key=key)

        try:
            record_metadata = future.get(timeout=10)
        except KafkaError:
            logger.exception("Error sending data to Kafka.")
            return False
        except Exception:
            logger.exception("Error when sending data to Kafka.")
            return False
        else:
            if debug:
                logger.info("Sending to the Kafka is successful. "
                            f"topic = {record_metadata.topic}, "
                            f"partition = {record_metadata.partition}, "
                            f"offset = {record_metadata.offset}.")
            return True


if __name__ == '__main__':
    KAFKA_test = {
        'device': {
            'bootstrap_servers': ["192.168.1.81:9093",]
        }
    }
    topic, config = tuple(KAFKA_test.items())[0]

    pr1 = KafkaProd(topic=topic,
                    bootstrap_servers=config.get("bootstrap_servers"))
    pr2 = KafkaProd(topic=topic,
                    bootstrap_servers=config.get("bootstrap_servers"))
    if id(pr1) != id(pr2):
        print("class KafkaProd is not a Singleton!")
    else:
        print("class KafkaProd is a Singleton!")
