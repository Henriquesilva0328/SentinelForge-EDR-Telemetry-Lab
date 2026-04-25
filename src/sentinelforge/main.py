from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from sentinelforge.api.v1.router import api_router
from sentinelforge.core.logging import configure_logging
from sentinelforge.core.settings import get_settings
from sentinelforge.messaging.producer import get_kafka_producer_manager
from sentinelforge.middleware.request_context import RequestContextMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Controla startup e shutdown da aplicação.

    Nesta etapa iniciamos:
    - logging
    - producer Kafka
    """
    configure_logging()

    producer_manager = get_kafka_producer_manager()
    await producer_manager.start()

    try:
        yield
    finally:
        await producer_manager.stop()


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(RequestContextMiddleware)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """
    Endpoint raiz para smoke test simples.
    """
    return {
        "service": settings.service_name,
        "status": "running",
    }


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, _: Exception):
    """
    Evita vazar detalhes internos da aplicação para o cliente.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "internal server error",
            "request_id": request_id,
        },
    )