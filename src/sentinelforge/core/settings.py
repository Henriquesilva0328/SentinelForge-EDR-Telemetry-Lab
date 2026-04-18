from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centraliza as configurações da aplicação.

    Essa classe lê variáveis de ambiente e converte tudo para os tipos corretos.
    Isso evita espalhar leitura manual de env vars pelo projeto.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Metadados gerais da aplicação
    app_name: str = "SentinelForge EDR Ingest API"
    environment: Literal["local", "dev", "test", "prod"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    api_v1_prefix: str = "/api/v1"
    service_name: str = "ingest-api"

    # Token de autenticação do endpoint de ingestão no MVP
    ingest_shared_token: SecretStr = Field(
        default=SecretStr("replace-this-in-env")
    )

    # URL do banco, ainda não usada nesta fase, mas já preparada
    db_url: str = "postgresql+asyncpg://sentinel:sentinel@localhost:5432/sentinelforge"


@lru_cache
def get_settings() -> Settings:
    """
    Retorna uma instância única de configurações.
    """
    return Settings()