import logging

from sentinelforge.db.session import SessionFactory
from sentinelforge.models.ingest_rejection_audit import IngestRejectionAudit

logger = logging.getLogger(__name__)


async def record_ingest_rejection(
    *,
    request_id: str,
    path: str,
    reason: str,
    status_code: int,
    source_ip: str | None,
    user_agent: str | None,
) -> None:
    """
    Registra uma rejeição crítica da ingestão.

    Fazemos isso fora do fluxo principal de models de negócio,
    porque algumas rejeições acontecem antes do evento ser aceito.
    """
    try:
        async with SessionFactory() as session:
            row = IngestRejectionAudit(
                request_id=request_id,
                path=path,
                reason=reason,
                status_code=status_code,
                source_ip=source_ip,
                user_agent=user_agent,
            )
            session.add(row)
            await session.commit()
    except Exception:
        # Nunca queremos que falha de auditoria esconda
        # a resposta original da rejeição.
        logger.exception("failed to record ingest rejection audit")