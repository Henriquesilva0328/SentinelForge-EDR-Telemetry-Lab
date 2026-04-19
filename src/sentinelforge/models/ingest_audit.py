from datetime import datetime
from uuid import UUID as UUIDType

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from sentinelforge.db.base import Base


class IngestAudit(Base):
    __tablename__ = "ingest_audit"
    __table_args__ = (
        Index("ix_ingest_audit_event_id", "event_id"),
        Index("ix_ingest_audit_request_id", "request_id"),
        Index("ix_ingest_audit_decision", "decision"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=False),
        primary_key=True,
    )

    raw_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("raw_events.id", ondelete="SET NULL"),
        nullable=True,
    )

    event_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    source_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)

    auth_mechanism: Mapped[str] = mapped_column(
        String(64),
        default="bearer_shared_token",
        server_default="bearer_shared_token",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )