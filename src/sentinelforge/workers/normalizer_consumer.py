import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer

from sentinelforge.core.logging import configure_logging
from sentinelforge.core.settings import get_settings
from sentinelforge.db.session import SessionFactory
from sentinelforge.messaging.producer import get_kafka_producer_manager
from sentinelforge.observability.metrics import (
    observe_worker_message_result,
    set_worker_down,
    start_worker_metrics_server,
)
from sentinelforge.schemas.normalized import RawIngestedMessage
from sentinelforge.services.normalization_service import (
    normalize_raw_ingested_message,
    persist_normalized_event,
)
from sentinelforge.services.normalized_publish_service import publish_normalized_event

logger = logging.getLogger(__name__)


async def run() -> None:
    """
    Worker de normalização.

    Consome eventos brutos do Kafka, normaliza, persiste
    e republica o evento normalizado.
    """
    settings = get_settings()
    producer_manager = get_kafka_producer_manager()

    consumer = AIOKafkaConsumer(
        settings.kafka_topic_raw_ingested,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_consumer_group_normalizer,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )

    await consumer.start()
    await producer_manager.start()

    if settings.metrics_enabled:
        start_worker_metrics_server(
            worker="normalizer",
            port=settings.metrics_normalizer_port,
        )

    logger.info(
        "normalizer consumer started",
        extra={
            "topic": settings.kafka_topic_raw_ingested,
            "group_id": settings.kafka_consumer_group_normalizer,
            "bootstrap_servers": settings.kafka_bootstrap_servers,
        },
    )

    try:
        async for message in consumer:
            try:
                raw_payload = json.loads(message.value.decode("utf-8"))
                raw_message = RawIngestedMessage.model_validate(raw_payload)
                normalized_document = normalize_raw_ingested_message(raw_message)

                async with SessionFactory() as session:
                    result = await persist_normalized_event(
                        normalized_event=normalized_document,
                        session=session,
                    )

                if result.decision == "accepted" and result.normalized_event_id is not None:
                    await publish_normalized_event(
                        normalized_event=normalized_document,
                        normalized_event_id=result.normalized_event_id,
                    )

                await consumer.commit()

                observe_worker_message_result(
                    worker="normalizer",
                    result="success",
                )

                logger.info(
                    "raw ingested event normalized",
                    extra={
                        "topic": message.topic,
                        "partition": message.partition,
                        "offset": message.offset,
                        "raw_event_id": raw_message.raw_event_id,
                        "event_id": str(raw_message.event_id),
                        "decision": result.decision,
                        "normalized_event_id": result.normalized_event_id,
                    },
                )
            except Exception:
                observe_worker_message_result(
                    worker="normalizer",
                    result="error",
                )
                logger.exception("failed to normalize consumed event")
    finally:
        await consumer.stop()
        await producer_manager.stop()

        if settings.metrics_enabled:
            set_worker_down(worker="normalizer")

        logger.info("normalizer consumer stopped")


if __name__ == "__main__":
    configure_logging()
    asyncio.run(run())