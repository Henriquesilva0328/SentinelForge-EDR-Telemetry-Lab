from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from sentinelforge.db.base import Base


class AlertEvidence(Base):
    """
    Evidência associada a um alerta.

    Mantemos payload estruturado para explicar por que a regra disparou.
    """

    __tablename__ = "alert_evidence"
    __table_args__ = (
        Index("ix_alert_evidence_alert_id", "alert_id"),
        Index("ix_alert_evidence_evidence_type", "evidence_type"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=False),
        primary_key=True,
    )

    alert_id: Mapped[int] = mapped_column(
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False,
    )

    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )