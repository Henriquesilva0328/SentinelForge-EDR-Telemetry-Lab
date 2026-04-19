from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from sentinelforge.api.v1.deps import require_ingest_token
from sentinelforge.db.session import get_db_session
from sentinelforge.schemas.events import IngestAccepted, TelemetryEvent
from sentinelforge.services.ingest_service import accept_event

router = APIRouter(prefix="/events", tags=["ingest"])


@router.post(
    "",
    response_model=IngestAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_ingest_token)],
)
async def ingest_event(
    request: Request,
    event: TelemetryEvent,
    session: AsyncSession = Depends(get_db_session),
) -> IngestAccepted:
    """
    Recebe um evento validado e persiste a ingestão.

    Já capturamos metadados úteis da requisição para auditoria,
    como IP de origem e user-agent.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    source_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    await accept_event(
        event=event,
        request_id=request_id,
        source_ip=source_ip,
        user_agent=user_agent,
        session=session,
    )

    return IngestAccepted(status="accepted", event_id=event.event_id)