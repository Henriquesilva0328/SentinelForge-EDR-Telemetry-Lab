from fastapi import APIRouter, Depends, Request, status

from sentinelforge.api.v1.deps import require_ingest_token
from sentinelforge.schemas.events import IngestAccepted, TelemetryEvent
from sentinelforge.services.ingest_service import accept_event

router = APIRouter(prefix="/events", tags=["ingest"])


@router.post(
    "",
    response_model=IngestAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_ingest_token)],
)
async def ingest_event(request: Request, event: TelemetryEvent) -> IngestAccepted:
    """
    Recebe um evento validado, autentica a chamada e aceita o payload
    para processamento assíncrono futuro.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    await accept_event(event=event, request_id=request_id)
    return IngestAccepted(status="accepted", event_id=event.event_id)