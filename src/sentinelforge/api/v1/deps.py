import secrets

from fastapi import Header, HTTPException, Request, status

from sentinelforge.core.settings import get_settings
from sentinelforge.services.audit_service import record_ingest_rejection


async def require_json_content_type(request: Request) -> None:
    """
    Exige application/json no endpoint de ingestão.

    Isso reduz input torto ou envio acidental de formatos errados.
    """
    settings = get_settings()

    if not settings.require_json_content_type:
        return

    content_type = request.headers.get("content-type", "")
    if not content_type.startswith("application/json"):
        request_id = getattr(request.state, "request_id", request.headers.get("x-request-id", "unknown"))

        await record_ingest_rejection(
            request_id=request_id,
            path=request.url.path,
            reason="invalid content type",
            status_code=415,
            source_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="content-type must be application/json",
        )


async def require_ingest_token(
    request: Request,
    authorization: str | None = Header(default=None),
) -> None:
    """
    Protege o endpoint de ingestão usando Bearer token.

    Nesta etapa também auditamos rejeições de autenticação.
    """
    request_id = getattr(request.state, "request_id", request.headers.get("x-request-id", "unknown"))

    if not authorization or not authorization.startswith("Bearer "):
        await record_ingest_rejection(
            request_id=request_id,
            path=request.url.path,
            reason="missing bearer token",
            status_code=401,
            source_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
        )

    provided_token = authorization.removeprefix("Bearer ").strip()
    expected_token = get_settings().ingest_shared_token.get_secret_value()

    if not secrets.compare_digest(provided_token, expected_token):
        await record_ingest_rejection(
            request_id=request_id,
            path=request.url.path,
            reason="invalid bearer token",
            status_code=401,
            source_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid bearer token",
        )