from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from sentinelforge.api.v1.deps import require_ingest_token
from sentinelforge.db.session import get_db_session
from sentinelforge.observability.metrics import observe_ingest_result
from sentinelforge.schemas.events import IngestAccepted, TelemetryEvent
from sentinelforge.services.ingest_service import accept_event
from sentinelforge.services.publish_service import publish_raw_ingested_event

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
    request_id = getattr(request.state, "request_id", "unknown")
    source_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    persistence_result = await accept_event(
        event=event,
        request_id=request_id,
        source_ip=source_ip,
        user_agent=user_agent,
        session=session,
    )

    observe_ingest_result(
        decision=persistence_result.decision,
        category=event.category.value,
    )

    if persistence_result.decision == "accepted":
        await publish_raw_ingested_event(
            event=event,
            raw_event_id=persistence_result.raw_event_id,
            request_id=request_id,
        )

    return IngestAccepted(
        status="accepted",
        decision=persistence_result.decision,
        event_id=event.event_id,
    )