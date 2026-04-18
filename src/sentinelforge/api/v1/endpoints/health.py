from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def healthcheck() -> dict[str, str]:
    """
    Endpoint básico de saúde da aplicação.
    """
    return {"status": "ok"}