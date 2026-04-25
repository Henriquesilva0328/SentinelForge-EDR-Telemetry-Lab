import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer

from sentinelforge.core.logging import configure_logging
from sentinelforge.core.settings import get_settings

logger = logging.getLogger(__name__)


async def run() -> None:
    settings = get_settings()

    consumer = AIOKafkaConsumer(
        settings.kafka_topic_raw_ingested,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="sentinelforge-raw-ingest-debug",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )

    await consumer.start()
    logger.info(
        "raw ingest consumer started",
        extra={
            "topic": settings.kafka_topic_raw_ingested,
            "bootstrap_servers": settings.kafka_bootstrap_servers,
        },
    )

    try:
        async for message in consumer:
            payload = json.loads(message.value.decode("utf-8"))

            logger.info(
                "raw ingested event consumed",
                extra={
                    "topic": message.topic,
                    "partition": message.partition,
                    "offset": message.offset,
                    "event_id": payload.get("event_id"),
                    "raw_event_id": payload.get("raw_event_id"),
                    "tenant_id": payload.get("tenant_id"),
                    "category": payload.get("category"),
                },
            )
    finally:
        await consumer.stop()
        logger.info("raw ingest consumer stopped")


if __name__ == "__main__":
    configure_logging()
    asyncio.run(run())