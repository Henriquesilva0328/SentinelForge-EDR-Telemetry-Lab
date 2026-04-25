from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sentinelforge.schemas.events import AgentIdentity, EventCategory


class RawIngestedMessage(BaseModel):
    """
    Contrato consumido do tópico telemetry.raw.ingested.

    Essa estrutura representa o envelope publicado após a persistência
    do evento bruto no banco.
    """
    model_config = ConfigDict(extra="forbid")

    message_type: Literal["raw_ingested"]
    schema_version: Literal["1.0"]
    request_id: str = Field(min_length=1, max_length=128)
    event_id: UUID
    raw_event_id: int = Field(gt=0)
    tenant_id: str = Field(min_length=3, max_length=64)
    category: EventCategory
    occurred_at: datetime
    agent: AgentIdentity
    actor_user: str | None = Field(default=None, max_length=255)
    correlation_key: str | None = Field(default=None, max_length=255)
    payload: dict[str, Any]

    @field_validator("occurred_at")
    @classmethod
    def occurred_at_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must include timezone information")
        return value.astimezone(timezone.utc)


class NormalizedEventDocument(BaseModel):
    """
    Representação interna normalizada do evento.

    Aqui consolidamos o que interessa para correlação futura,
    sem depender do shape original do payload bruto.
    """
    model_config = ConfigDict(extra="forbid")

    normalization_version: Literal["1.0"]
    raw_event_id: int = Field(gt=0)
    event_id: UUID
    tenant_id: str
    category: EventCategory
    event_action: str
    occurred_at: datetime

    agent_id: str
    host_id: str
    hostname: str
    platform: str
    sensor_version: str

    actor_user: str | None = None
    correlation_key: str | None = None

    process_name: str | None = None
    process_pid: int | None = None
    file_path: str | None = None
    destination_ip: str | None = None
    destination_port: int | None = None
    auth_result: str | None = None

    normalized_payload: dict[str, Any]