from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from sentinelforge.api.v1.router import api_router
from sentinelforge.core.logging import configure_logging
from sentinelforge.core.settings import get_settings
from sentinelforge.messaging.producer import get_kafka_producer_manager
from sentinelforge.middleware.request_context import RequestContextMiddleware
from sentinelforge.middleware.security import (
    RequestBodyLimitMiddleware,
    SecurityHeadersMiddleware,
)
from sentinelforge.observability.metrics import observe_http_request
from sentinelforge.services.audit_service import record_ingest_rejection

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Startup e shutdown da aplicação.

    Também aplicamos uma checagem simples de segurança:
    em produção, não aceitamos subir com o token default.
    """
    configure_logging()

    if settings.environment == "prod":
        if settings.ingest_shared_token.get_secret_value() == "sentinel-ingest-dev-token":
            raise RuntimeError("refusing to start in prod with default ingest token")

    producer_manager = get_kafka_producer_manager()
    await producer_manager.start()

    try:
        yield
    finally:
        await producer_manager.stop()


# Docs só ficam ligadas em local/dev.
docs_enabled = settings.environment in {"local", "dev"}

app = FastAPI(
    title=settings.app_name,
    version="0.8.0",
    lifespan=lifespan,
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
)

app.add_middleware(RequestContextMiddleware)
app.add_middleware(RequestBodyLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.middleware("http")
async def prometheus_http_metrics(request: Request, call_next):
    """
    Middleware de métricas HTTP.
    """
    started = perf_counter()
    response = None

    try:
        response = await call_next(request)
        return response
    finally:
        duration_seconds = perf_counter() - started
        status_code = response.status_code if response is not None else 500

        observe_http_request(
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_seconds=duration_seconds,
        )


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    return {
        "service": settings.service_name,
        "status": "running",
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Padroniza erro de validação sem vazar detalhe desnecessário
    e audita falhas de validação no endpoint de ingestão.
    """
    request_id = getattr(request.state, "request_id", "unknown")

    if request.url.path == f"{settings.api_v1_prefix}/events":
        await record_ingest_rejection(
            request_id=request_id,
            path=request.url.path,
            reason="validation error",
            status_code=422,
            source_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

    return JSONResponse(
        status_code=422,
        content={
            "detail": "validation error",
            "request_id": request_id,
            "errors": exc.errors(),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Padroniza respostas de HTTPException.
    """
    request_id = getattr(request.state, "request_id", "unknown")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "request_id": request_id,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, _: Exception):
    """
    Evita vazar exceções internas em resposta HTTP.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "internal server error",
            "request_id": request_id,
        },
    )