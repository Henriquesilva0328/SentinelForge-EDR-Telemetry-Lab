import logging

from sentinelforge.core.settings import get_settings
from sentinelforge.messaging.producer import get_kafka_producer_manager
from sentinelforge.observability.metrics import observe_kafka_publish
from sentinelforge.schemas.events import TelemetryEvent

logger = logging.getLogger(__name__)


async def publish_raw_ingested_event(
    *,
    event: TelemetryEvent,
    raw_event_id: int,
    request_id: str,
) -> None:
    """
    Publica o evento bruto ingerido para o próximo estágio do pipeline.

    Registra métrica de sucesso ou erro da publicação.
    """
    settings = get_settings()
    producer_manager = get_kafka_producer_manager()

    message = {
        "message_type": "raw_ingested",
        "schema_version": "1.0",
        "request_id": request_id,
        "event_id": str(event.event_id),
        "raw_event_id": raw_event_id,
        "tenant_id": event.tenant_id,
        "category": event.category.value,
        "occurred_at": event.occurred_at.isoformat(),
        "agent": {
            "agent_id": event.agent.agent_id,
            "host_id": event.agent.host_id,
            "hostname": event.agent.hostname,
            "platform": event.agent.platform,
            "sensor_version": event.agent.sensor_version,
        },
        "actor_user": event.actor_user,
        "correlation_key": event.correlation_key,
        "payload": event.payload,
    }

    try:
        metadata = await producer_manager.send_json(
            topic=settings.kafka_topic_raw_ingested,
            key=str(event.event_id),
            value=message,
            headers=[
                ("message_type", b"raw_ingested"),
                ("schema_version", b"1.0"),
            ],
        )

        observe_kafka_publish(
            topic=settings.kafka_topic_raw_ingested,
            result="success",
        )

        logger.info(
            "telemetry event published to kafka",
            extra={
                "request_id": request_id,
                "event_id": str(event.event_id),
                "raw_event_id": raw_event_id,
                "topic": metadata.topic,
                "partition": metadata.partition,
                "offset": metadata.offset,
            },
        )
    except Exception:
        observe_kafka_publish(
            topic=settings.kafka_topic_raw_ingested,
            result="error",
        )
        raise