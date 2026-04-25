from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from sentinelforge.core.settings import get_settings
from sentinelforge.services.audit_service import record_ingest_rejection


class RequestBodyLimitMiddleware(BaseHTTPMiddleware):
    """
    Limita o tamanho do corpo da request.

    Isso evita abuso básico de payload gigante no endpoint de ingestão.
    A checagem é focada no caminho /api/v1/events, onde entra telemetria.
    """

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        ingest_path = f"{settings.api_v1_prefix}/events"

        if request.url.path == ingest_path:
            request_id = getattr(request.state, "request_id", request.headers.get("x-request-id", "unknown"))
            content_length = request.headers.get("content-length")

            # Primeiro tentamos um corte barato pelo header.
            if content_length is not None:
                try:
                    if int(content_length) > settings.max_request_body_bytes:
                        await record_ingest_rejection(
                            request_id=request_id,
                            path=request.url.path,
                            reason="request body too large",
                            status_code=413,
                            source_ip=request.client.host if request.client else None,
                            user_agent=request.headers.get("user-agent"),
                        )
                        return JSONResponse(
                            status_code=413,
                            content={
                                "detail": "request body too large",
                                "request_id": request_id,
                            },
                        )
                except ValueError:
                    # Se o header vier malformado, seguimos para a leitura real do body.
                    pass

            # Se não confiarmos no header, lemos o body e validamos pelo tamanho real.
            body = await request.body()
            if len(body) > settings.max_request_body_bytes:
                await record_ingest_rejection(
                    request_id=request_id,
                    path=request.url.path,
                    reason="request body too large",
                    status_code=413,
                    source_ip=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                )
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": "request body too large",
                        "request_id": request_id,
                    },
                )

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injeta headers básicos de segurança nas respostas HTTP.

    Isso não transforma o lab num bunker, mas já evita
    um monte de descuido básico de exposição.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        settings = get_settings()
        if settings.security_headers_enabled:
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Referrer-Policy"] = "no-referrer"
            response.headers["Cache-Control"] = "no-store"

        return response