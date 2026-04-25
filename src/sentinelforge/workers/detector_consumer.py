import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer

from sentinelforge.core.logging import configure_logging
from sentinelforge.core.settings import get_settings
from sentinelforge.db.session import SessionFactory
from sentinelforge.observability.metrics import (
    observe_detection_match,
    observe_worker_message_result,
    set_worker_down,
    start_worker_metrics_server,
)
from sentinelforge.schemas.normalized import NormalizedPublishedMessage
from sentinelforge.services.alert_service import persist_alerts
from sentinelforge.services.detection_service import evaluate_normalized_event

logger = logging.getLogger(__name__)


async def run() -> None:
    """
    Worker detector.

    Consome eventos normalizados do Kafka, aplica regras
    e persiste alertas/evidências quando houver match.
    """
    settings = get_settings()

    consumer = AIOKafkaConsumer(
        settings.kafka_topic_normalized,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_consumer_group_detector,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )

    await consumer.start()

    if settings.metrics_enabled:
        start_worker_metrics_server(
            worker="detector",
            port=settings.metrics_detector_port,
        )

    logger.info(
        "detector consumer started",
        extra={
            "topic": settings.kafka_topic_normalized,
            "group_id": settings.kafka_consumer_group_detector,
            "bootstrap_servers": settings.kafka_bootstrap_servers,
        },
    )

    try:
        async for message in consumer:
            try:
                raw_payload = json.loads(message.value.decode("utf-8"))
                normalized_message = NormalizedPublishedMessage.model_validate(raw_payload)

                matches = evaluate_normalized_event(normalized_message)

                for match in matches:
                    observe_detection_match(
                        rule_id=match.rule_id,
                        severity=match.severity,
                    )

                if matches:
                    async with SessionFactory() as session:
                        summary = await persist_alerts(
                            normalized_message=normalized_message,
                            matches=matches,
                            session=session,
                        )

                    logger.info(
                        "normalized event produced detection matches",
                        extra={
                            "normalized_event_id": normalized_message.normalized_event_id,
                            "event_id": str(normalized_message.event_id),
                            "created_alerts": summary.created_count,
                            "duplicate_alerts": summary.duplicate_count,
                        },
                    )
                else:
                    logger.info(
                        "normalized event produced no alerts",
                        extra={
                            "normalized_event_id": normalized_message.normalized_event_id,
                            "event_id": str(normalized_message.event_id),
                        },
                    )

                await consumer.commit()

                observe_worker_message_result(
                    worker="detector",
                    result="success",
                )
            except Exception:
                observe_worker_message_result(
                    worker="detector",
                    result="error",
                )
                logger.exception("failed to process normalized event in detector")
    finally:
        await consumer.stop()

        if settings.metrics_enabled:
            set_worker_down(worker="detector")

        logger.info("detector consumer stopped")


if __name__ == "__main__":
    configure_logging()
    asyncio.run(run())