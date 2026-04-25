from datetime import datetime
from uuid import UUID as UUIDType

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from sentinelforge.db.base import Base


class NormalizedEvent(Base):
    """
    Evento interno normalizado derivado de raw_events.

    Um raw_event deve gerar no máximo um normalized_event.
    Por isso raw_event_id é único.
    """

    __tablename__ = "normalized_events"
    __table_args__ = (
        Index("ix_normalized_events_tenant_id", "tenant_id"),
        Index("ix_normalized_events_category", "category"),
        Index("ix_normalized_events_occurred_at", "occurred_at"),
        Index("ix_normalized_events_event_action", "event_action"),
        Index("ix_normalized_events_hostname", "hostname"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=False),
        primary_key=True,
    )

    raw_event_id: Mapped[int] = mapped_column(
        ForeignKey("raw_events.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    event_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    normalization_version: Mapped[str] = mapped_column(String(16), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    event_action: Mapped[str] = mapped_column(String(64), nullable=False)

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    normalized_at: Mapped[datetime] = mapped_column(
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

    process_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    process_pid: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    destination_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    destination_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    auth_result: Mapped[str | None] = mapped_column(String(64), nullable=True)

    normalized_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)