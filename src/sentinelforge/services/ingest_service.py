import logging

from sentinelforge.schemas.events import TelemetryEvent

logger = logging.getLogger(__name__)


async def accept_event(event: TelemetryEvent, request_id: str) -> None:
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
        },
    )