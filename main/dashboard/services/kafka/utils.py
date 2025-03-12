import json
import logging
import time
from kafka import KafkaConsumer
from main.settings import KAFKA


logger = logging.getLogger(__name__)


def get_latest_topic_value(topic: str):
    """Get latest message value from kafka topic.

    Return None, if no messages in topic or kafka is available or another error raised.
    """

    try:
        consumer: KafkaConsumer = KafkaConsumer(
            topic,
            bootstrap_servers=[KAFKA],
            enable_auto_commit=False,
            auto_offset_reset="earliest",
            consumer_timeout_ms=3000,
        )
    except Exception as e:
        logger.warning(f"Unable to create consumer for topic `{topic}`. {e}")
        return None

    latest_message = None
    while True:
        try:
            latest_message = consumer.next_v2()
            time.sleep(0.01)
        except Exception:
            break

    if latest_message is None:
        return None

    try:
        return json.loads(latest_message.value.decode('utf-8'))
    except Exception as e:
        logger.error(f"{e}. Error when parsing value from latest kafka message, {topic=}, {latest_message.value=}")
        return None
