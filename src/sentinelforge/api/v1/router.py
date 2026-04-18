from fastapi import APIRouter

from sentinelforge.api.v1.endpoints.health import router as health_router
from sentinelforge.api.v1.endpoints.ingest import router as ingest_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(ingest_router)