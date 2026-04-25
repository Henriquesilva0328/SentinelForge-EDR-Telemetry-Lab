import logging
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sentinelforge.core.settings import get_settings
from sentinelforge.models.normalized_event import NormalizedEvent
from sentinelforge.schemas.events import EventCategory
from sentinelforge.schemas.normalized import NormalizedEventDocument, RawIngestedMessage

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class NormalizationPersistenceResult:
    decision: Literal["accepted", "duplicate"]
    normalized_event_id: int | None


def normalize_raw_ingested_message(
    message: RawIngestedMessage,
) -> NormalizedEventDocument:
    """
    Converte a mensagem bruta ingerida em um formato interno previsível.

    A lógica aqui ainda é simples, mas já separa o contrato bruto
    da representação que o pipeline vai usar nas próximas etapas.
    """
    settings = get_settings()

    event_action = "unknown"
    process_name = None
    process_pid = None
    file_path = None
    destination_ip = None
    destination_port = None
    auth_result = None

    if message.category == EventCategory.PROCESS:
        event_action = "process_start"
        process_name = _safe_str(message.payload.get("process_name"))
        process_pid = _safe_int(message.payload.get("pid"))

    elif message.category == EventCategory.NETWORK:
        event_action = _safe_str(message.payload.get("action")) or "network_connection"
        destination_ip = (
            _safe_str(message.payload.get("destination_ip"))
            or _safe_str(message.payload.get("dst_ip"))
        )
        destination_port = (
            _safe_int(message.payload.get("destination_port"))
            or _safe_int(message.payload.get("dst_port"))
        )

    elif message.category == EventCategory.FILE:
        event_action = _safe_str(message.payload.get("action")) or "file_activity"
        file_path = (
            _safe_str(message.payload.get("file_path"))
            or _safe_str(message.payload.get("path"))
        )

    elif message.category == EventCategory.AUTH:
        event_action = "authentication"
        auth_result = (
            _safe_str(message.payload.get("result"))
            or _safe_str(message.payload.get("status"))
            or "unknown"
        )

    normalized_payload = {
        "source_message_type": message.message_type,
        "source_schema_version": message.schema_version,
        "normalization_version": settings.normalization_version,
        "request_id": message.request_id,
        "agent": {
            "agent_id": message.agent.agent_id,
            "host_id": message.agent.host_id,
            "hostname": message.agent.hostname,
            "platform": message.agent.platform,
            "sensor_version": message.agent.sensor_version,
        },
        "category": message.category.value,
        "event_action": event_action,
        "payload": message.payload,
    }

    return NormalizedEventDocument(
        normalization_version=settings.normalization_version,
        raw_event_id=message.raw_event_id,
        event_id=message.event_id,
        tenant_id=message.tenant_id,
        category=message.category,
        event_action=event_action,
        occurred_at=message.occurred_at,
        agent_id=message.agent.agent_id,
        host_id=message.agent.host_id,
        hostname=message.agent.hostname,
        platform=message.agent.platform,
        sensor_version=message.agent.sensor_version,
        actor_user=message.actor_user,
        correlation_key=message.correlation_key,
        process_name=process_name,
        process_pid=process_pid,
        file_path=file_path,
        destination_ip=destination_ip,
        destination_port=destination_port,
        auth_result=auth_result,
        normalized_payload=normalized_payload,
    )


async def persist_normalized_event(
    *,
    normalized_event: NormalizedEventDocument,
    session: AsyncSession,
) -> NormalizationPersistenceResult:
    """
    Persiste o evento normalizado.

    A unicidade por raw_event_id garante que o replay ou reconsumo
    do Kafka não gere múltiplos registros da mesma normalização.
    """
    existing_id = await session.scalar(
        select(NormalizedEvent.id).where(
            NormalizedEvent.raw_event_id == normalized_event.raw_event_id
        )
    )

    if existing_id is not None:
        logger.info(
            "normalized event already exists",
            extra={
                "raw_event_id": normalized_event.raw_event_id,
                "event_id": str(normalized_event.event_id),
                "normalized_event_id": existing_id,
            },
        )
        return NormalizationPersistenceResult(
            decision="duplicate",
            normalized_event_id=existing_id,
        )

    db_event = NormalizedEvent(
        raw_event_id=normalized_event.raw_event_id,
        event_id=normalized_event.event_id,
        normalization_version=normalized_event.normalization_version,
        tenant_id=normalized_event.tenant_id,
        category=normalized_event.category.value,
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

    session.add(db_event)
    await session.flush()
    await session.commit()

    logger.info(
        "normalized event persisted",
        extra={
            "raw_event_id": normalized_event.raw_event_id,
            "event_id": str(normalized_event.event_id),
            "normalized_event_id": db_event.id,
            "category": normalized_event.category.value,
            "event_action": normalized_event.event_action,
        },
    )

    return NormalizationPersistenceResult(
        decision="accepted",
        normalized_event_id=db_event.id,
    )


def _safe_str(value) -> str | None:
    if value is None:
        return None
    return str(value)


def _safe_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None