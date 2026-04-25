from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sentinelforge.core.settings import get_settings


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

    Nesta etapa endurecemos a validação do payload para:
    - limitar profundidade
    - limitar quantidade de chaves/itens
    - limitar tamanho de strings
    - impedir tipos estranhos não previstos
    """
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    # O event_id vem do produtor e é essencial para deduplicação.
    event_id: UUID

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
        Obriga timezone explícito e converte tudo para UTC.
        """
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must include timezone information")

        return value.astimezone(timezone.utc)

    @field_validator("payload")
    @classmethod
    def payload_must_respect_security_limits(cls, value: dict[str, Any]) -> dict[str, Any]:
        """
        Valida recursivamente a estrutura do payload.

        Isso reduz:
        - payloads absurdamente grandes
        - nesting abusivo
        - strings gigantes
        - tipos não esperados
        """
        settings = get_settings()
        _validate_payload_node(
            node=value,
            depth=1,
            max_depth=settings.telemetry_payload_max_depth,
            max_keys=settings.telemetry_payload_max_keys,
            max_items=settings.telemetry_payload_max_items,
            max_string_length=settings.telemetry_payload_max_string_length,
        )
        return value


class IngestAccepted(BaseModel):
    """
    Resposta da API após avaliar a ingestão.

    status indica que a API recebeu e tratou a requisição.
    decision indica se o evento foi novo ou duplicado.
    """
    status: Literal["accepted"]
    decision: Literal["accepted", "duplicate"]
    event_id: UUID


def _validate_payload_node(
    *,
    node: Any,
    depth: int,
    max_depth: int,
    max_keys: int,
    max_items: int,
    max_string_length: int,
) -> None:
    """
    Faz a validação recursiva do payload.

    Regras:
    - dicts: limite de chaves
    - listas: limite de itens
    - strings: limite de tamanho
    - profundidade: limite máximo
    - tipos permitidos: dict, list, str, int, float, bool, None
    """
    if depth > max_depth:
        raise ValueError("payload nesting exceeds allowed depth")

    if isinstance(node, dict):
        if len(node) > max_keys:
            raise ValueError("payload contains too many keys")

        for key, value in node.items():
            if not isinstance(key, str):
                raise ValueError("payload keys must be strings")

            if len(key) > 128:
                raise ValueError("payload key length exceeds allowed limit")

            _validate_payload_node(
                node=value,
                depth=depth + 1,
                max_depth=max_depth,
                max_keys=max_keys,
                max_items=max_items,
                max_string_length=max_string_length,
            )
        return

    if isinstance(node, list):
        if len(node) > max_items:
            raise ValueError("payload list contains too many items")

        for item in node:
            _validate_payload_node(
                node=item,
                depth=depth + 1,
                max_depth=max_depth,
                max_keys=max_keys,
                max_items=max_items,
                max_string_length=max_string_length,
            )
        return

    if isinstance(node, str):
        if len(node) > max_string_length:
            raise ValueError("payload string length exceeds allowed limit")
        return

    if isinstance(node, (int, float, bool)) or node is None:
        return

    raise ValueError("payload contains unsupported value type")