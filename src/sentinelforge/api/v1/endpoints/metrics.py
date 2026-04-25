from fastapi import APIRouter, Response

from sentinelforge.observability.metrics import (
    generate_metrics_payload,
    metrics_content_type,
)

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("", include_in_schema=False)
async def metrics() -> Response:
    return Response(
        content=generate_metrics_payload(),
        media_type=metrics_content_type(),
    )