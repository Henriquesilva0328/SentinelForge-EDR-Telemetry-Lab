from datetime import datetime
from uuid import UUID as UUIDType, uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from sentinelforge.db.base import Base


class Alert(Base):
    """
    Alerta gerado pelo motor de regras.

    A unicidade por (rule_id, normalized_event_id) impede
    que o mesmo evento gere o mesmo alerta múltiplas vezes
    em caso de reprocessamento.
    """

    __tablename__ = "alerts"
    __table_args__ = (
        UniqueConstraint("rule_id", "normalized_event_id", name="uq_alerts_rule_id_normalized_event_id"),
        Index("ix_alerts_tenant_id", "tenant_id"),
        Index("ix_alerts_rule_id", "rule_id"),
        Index("ix_alerts_severity", "severity"),
        Index("ix_alerts_status", "status"),
        Index("ix_alerts_hostname", "hostname"),
        Index("ix_alerts_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=False),
        primary_key=True,
    )

    alert_uid: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
        default=uuid4,
    )

    normalized_event_id: Mapped[int] = mapped_column(
        ForeignKey("normalized_events.id", ondelete="CASCADE"),
        nullable=False,
    )

    raw_event_id: Mapped[int] = mapped_column(
        ForeignKey("raw_events.id", ondelete="CASCADE"),
        nullable=False,
    )

    event_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="open",
        server_default="open",
    )

    agent_id: Mapped[str] = mapped_column(String(64), nullable=False)
    host_id: Mapped[str] = mapped_column(String(128), nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_user: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )