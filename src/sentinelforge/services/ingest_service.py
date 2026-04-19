import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sentinelforge.models import IngestAudit, RawEvent

from sentinelforge.schemas.events import TelemetryEvent

logger = logging.getLogger(__name__)


async def accept_event(
        *,
        event: TelemetryEvent, 
        request_id: str,
        source_ip: str | None,
        user_agent: str | None,
        session: AsyncSession,
) -> None:
    """
    Persiste o evento bruto e a trilha de auditoria da ingestão.

    Se o event_id já existir, tratamos como duplicado e registramos
    isso em auditoria sem quebrar a API. Em pipeline orientado a eventos,
    idempotência básica evita muito ruído operacional.
    """
    existing_raw_event_id = await session.scalar(
        select(RawEvent.id).where(RawEvent.event_id == event.event_id)
    )

    if existing_raw_event_id is not None:
        duplicate_audit = IngestAudit(
            raw_event_id=existing_raw_event_id,
            event_id=event.event_id,
            request_id=request_id,
            decision="duplicate",
            reason="event_id already processed",
            source_ip=source_ip,
            user_agent=user_agent,
        )
        session.add(duplicate_audit)
        await session.commit()

        logger.info(
            "duplicate telemetry event ignored",
            extra={
                "request_id": request_id,
                "event_id": str(event.event_id),
                "tenant_id": event.tenant_id,
                "category": event.category.value,
                "agent_id": event.agent.agent_id,
            },
        )
        return

    raw_event = RawEvent(
        event_id=event.event_id,
        schema_version=event.schema_version,
        tenant_id=event.tenant_id,
        category=event.category.value,
        occurred_at=event.occurred_at,
        agent_id=event.agent.agent_id,
        host_id=event.agent.host_id,
        hostname=event.agent.hostname,
        platform=event.agent.platform,
        sensor_version=event.agent.sensor_version,
        actor_user=event.actor_user,
        correlation_key=event.correlation_key,
        payload=event.payload,
        ingestion_status="accepted",
    )

    session.add(raw_event)

    # flush envia o INSERT sem fechar a transação, permitindo
    # obter o id gerado para vincular a auditoria.
    await session.flush()

    audit_entry = IngestAudit(
        raw_event_id=raw_event.id,
        event_id=event.event_id,
        request_id=request_id,
        decision="accepted",
        reason=None,
        source_ip=source_ip,
        user_agent=user_agent,
    )
    session.add(audit_entry)

    await session.commit()
    """
    Serviço de ingestão da fase inicial.

    Nesta entrega ele apenas registra o aceite do evento.
    Depois vamos persistir em banco, publicar em Kafka
    e abrir trilha de auditoria.
    """
    logger.info(
        "telemetry event accepted",
        extra={
            "request_id": request_id,
            "event_id": str(event.event_id),
            "tenant_id": event.tenant_id,
            "category": event.category.value,
            "agent_id": event.agent.agent_id,
            "raw_event_id": raw_event.id,
        },
    )