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
        default=SecretStr("sentinel-ingest-dev-token")
    )

    # URL do banco
    db_url: str = "postgresql+asyncpg://sentinel:sentinel1@localhost:5433/sentinelforge"

    # URL usada pelo Alembic para migrations
    db_migration_url: str = "postgresql+psycopg://sentinel:sentinel1@localhost:5433/sentinelforge"

    kafka_enabled: bool = True
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_client_id: str = "sentinelforge-ingest-api"
    kafka_topic_raw_ingested: str = "telemetry.raw.ingested"
    kafka_topic_normalized: str = "telemetry.normalized"

    kafka_consumer_group_normalizer: str = "sentinelforge-normalizer"
    kafka_consumer_group_detector: str = "sentinelforge-detector"

    normalization_version: str = "1.0"

    metrics_enabled: bool = True
    metrics_normalizer_port: int = 9101
    metrics_detector_port: int = 9102

    # Tempo de espera para o pipeline assíncrono “assentar”
    # depois que o replay envia os eventos.
    replay_settle_seconds: float = 4.0

    # Diretório onde os relatórios do replay serão gravados.
    replay_output_dir: str = "artifacts/replay"

@lru_cache
def get_settings() -> Settings:
    """
    Retorna uma instância única de configurações.
    """
    return Settings()