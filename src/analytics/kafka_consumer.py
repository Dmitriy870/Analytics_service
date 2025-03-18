import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer

from analytics.dependencies import get_analytics_service
from analytics.schema import EventType
from analytics.service import AnalyticsService
from config import KafkaConfig

kafka_config = KafkaConfig()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def consume_messages(topic: str):
    logger.info("Initializing Kafka Consumer...")
    service: AnalyticsService = await get_analytics_service()

    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=kafka_config.BOOTSTRAP_SERVERS,
        group_id=kafka_config.GROUP_ID,
        auto_offset_reset=kafka_config.AUTO_OFFSET_RESET,
        enable_auto_commit=kafka_config.ENABLE_AUTO_COMMIT,
    )

    logger.info("Kafka consumer created. Attempting to start...")

    await consumer.start()
    logger.info("Kafka consumer started successfully and listening to topics: %s", topic)

    try:
        async for msg in consumer:
            try:
                event_data = json.loads(msg.value.decode("utf-8"))
                logger.info("Consumed from '%s': %s", msg.topic, event_data)
                event_data["event_type"] = EventType.MODEL
                logger.info("before process_event")
                await service.process_event(event_data)
                logger.info("After processing event data call")
            except json.JSONDecodeError:
                logger.error("Failed to decode message: %s", msg.value)
    except asyncio.CancelledError:
        logger.info("Consumer was cancelled.")
    finally:
        logger.info("Stopping consumer...")
        await consumer.stop()
        logger.info("Consumer stopped.")
