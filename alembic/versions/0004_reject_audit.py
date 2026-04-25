"""create ingest rejection audit table

Revision ID: 0004_reject_audit
Revises: 0003_alerts
Create Date: 2026-04-25
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0004_reject_audit"
down_revision: str | None = "0003_alerts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ingest_rejection_audit",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("source_ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_index(
        "ix_ingest_rejection_audit_request_id",
        "ingest_rejection_audit",
        ["request_id"],
        unique=False,
    )
    op.create_index(
        "ix_ingest_rejection_audit_status_code",
        "ingest_rejection_audit",
        ["status_code"],
        unique=False,
    )
    op.create_index(
        "ix_ingest_rejection_audit_path",
        "ingest_rejection_audit",
        ["path"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ingest_rejection_audit_path", table_name="ingest_rejection_audit")
    op.drop_index("ix_ingest_rejection_audit_status_code", table_name="ingest_rejection_audit")
    op.drop_index("ix_ingest_rejection_audit_request_id", table_name="ingest_rejection_audit")
    op.drop_table("ingest_rejection_audit")