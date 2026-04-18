from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventCategory(StrEnum):
    """
    Categorias suportadas de eventos de telemetria.
    """
    PROCESS = "process"
    NETWORK = "network"
    FILE = "file"
    AUTH = "auth"


class AgentIdentity(BaseModel):
    """
    Identidade do agente que gerou o evento.
    """
    model_config = ConfigDict(extra="forbid")

    agent_id: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9._-]+$")
    host_id: str = Field(min_length=3, max_length=128)
    hostname: str = Field(min_length=1, max_length=255)
    platform: str = Field(min_length=1, max_length=32)
    sensor_version: str = Field(min_length=1, max_length=32)


class TelemetryEvent(BaseModel):
    """
    Contrato principal de ingestão.

    Este schema representa a estrutura validada do evento recebido pela API.
    """
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    event_id: UUID = Field(default_factory=uuid4)
    tenant_id: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9._-]+$")
    category: EventCategory
    occurred_at: datetime
    agent: AgentIdentity
    actor_user: str | None = Field(default=None, max_length=255)
    correlation_key: str | None = Field(default=None, max_length=255)
    payload: dict[str, Any]

    @field_validator("occurred_at")
    @classmethod
    def occurred_at_must_be_timezone_aware(cls, value: datetime) -> datetime:
        """
        Garante que o timestamp tenha timezone explícito
        e normaliza tudo para UTC.
        """
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must include timezone information")

        return value.astimezone(timezone.utc)


class IngestAccepted(BaseModel):
    """
    Resposta da API quando o evento é aceito para processamento.
    """
    status: Literal["accepted"]
    event_id: UUID