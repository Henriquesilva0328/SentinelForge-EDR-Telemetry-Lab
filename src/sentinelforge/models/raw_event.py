from datetime import datetime
from uuid import UUID as UUIDType

from sqlalchemy import BigInteger, DateTime, Identity, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from sentinelforge.db.base import Base


class RawEvent(Base):
    """
    Armazena o evento bruto recebido pela API.

    Essa tabela é a trilha de verdade da ingestão.
    Mesmo antes de normalizar ou correlacionar, guardamos
    o payload original validado para auditoria e replay.
    """

    __tablename__ = "raw_events"
    __table_args__ = (
        Index("ix_raw_events_tenant_id", "tenant_id"),
        Index("ix_raw_events_category", "category"),
        Index("ix_raw_events_occurred_at", "occurred_at"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=False),
        primary_key=True,
    )

    # event_id vem do contrato de ingestão e precisa ser único
    # para termos idempotência básica.
    event_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
    )

    schema_version: Mapped[str] = mapped_column(String(16), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    agent_id: Mapped[str] = mapped_column(String(64), nullable=False)
    host_id: Mapped[str] = mapped_column(String(128), nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    sensor_version: Mapped[str] = mapped_column(String(32), nullable=False)

    actor_user: Mapped[str | None] = mapped_column(String(255), nullable=True)
    correlation_key: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Guardamos apenas o payload variável aqui.
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    ingestion_status: Mapped[str] = mapped_column(
        String(32),
        default="accepted",
        server_default="accepted",
        nullable=False,
    )