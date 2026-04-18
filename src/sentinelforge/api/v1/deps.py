import secrets

from fastapi import Header, HTTPException, status

from sentinelforge.core.settings import get_settings


async def require_ingest_token(
    authorization: str | None = Header(default=None),
) -> None:
    """
    Protege o endpoint de ingestão usando Bearer token.

    Nesta fase usamos um token compartilhado simples, suficiente
    para o laboratório local.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
        )

    provided_token = authorization.removeprefix("Bearer ").strip()
    expected_token = get_settings().ingest_shared_token.get_secret_value()

    if not secrets.compare_digest(provided_token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid bearer token",
        )