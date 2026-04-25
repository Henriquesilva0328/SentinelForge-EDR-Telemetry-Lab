import logging

from sentinelforge.core.settings import get_settings
from sentinelforge.messaging.producer import get_kafka_producer_manager
from sentinelforge.schemas.normalized import NormalizedEventDocument, NormalizedPublishedMessage

logger = logging.getLogger(__name__)


async def publish_normalized_event(
    *,
    normalized_event: NormalizedEventDocument,
    normalized_event_id: int,
) -> None:
    """
    Publica o evento normalizado no Kafka para a etapa de detecção.
    """
    settings = get_settings()
    producer_manager = get_kafka_producer_manager()

    message = NormalizedPublishedMessage(
        normalization_version="1.0",
        normalized_event_id=normalized_event_id,
        raw_event_id=normalized_event.raw_event_id,
        event_id=normalized_event.event_id,
        tenant_id=normalized_event.tenant_id,
        category=normalized_event.category,
        event_action=normalized_event.event_action,
        occurred_at=normalized_event.occurred_at,
        agent_id=normalized_event.agent_id,
        host_id=normalized_event.host_id,
        hostname=normalized_event.hostname,
        platform=normalized_event.platform,
        sensor_version=normalized_event.sensor_version,
        actor_user=normalized_event.actor_user,
        correlation_key=normalized_event.correlation_key,
        process_name=normalized_event.process_name,
        process_pid=normalized_event.process_pid,
        file_path=normalized_event.file_path,
        destination_ip=normalized_event.destination_ip,
        destination_port=normalized_event.destination_port,
        auth_result=normalized_event.auth_result,
        normalized_payload=normalized_event.normalized_payload,
    )

    metadata = await producer_manager.send_json(
        topic=settings.kafka_topic_normalized,
        key=str(normalized_event.event_id),
        value=message.model_dump(mode="json"),
        headers=[
            ("message_type", b"normalized_event"),
            ("normalization_version", b"1.0"),
        ],
    )

    logger.info(
        "normalized event published to kafka",
        extra={
            "normalized_event_id": normalized_event_id,
            "raw_event_id": normalized_event.raw_event_id,
            "event_id": str(normalized_event.event_id),
            "topic": metadata.topic,
            "partition": metadata.partition,
            "offset": metadata.offset,
        },
    )