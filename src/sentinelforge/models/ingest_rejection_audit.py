from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Identity, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from sentinelforge.db.base import Base


class IngestRejectionAudit(Base):
    """
    Auditoria de rejeições críticas da ingestão.

    Aqui guardamos rejeições importantes antes mesmo do evento
    entrar no pipeline normal, como:
    - token ausente/inválido
    - content-type inválido
    - body grande demais
    - erro de validação
    """

    __tablename__ = "ingest_rejection_audit"
    __table_args__ = (
        Index("ix_ingest_rejection_audit_request_id", "request_id"),
        Index("ix_ingest_rejection_audit_status_code", "status_code"),
        Index("ix_ingest_rejection_audit_path", "path"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=False),
        primary_key=True,
    )

    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    source_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )