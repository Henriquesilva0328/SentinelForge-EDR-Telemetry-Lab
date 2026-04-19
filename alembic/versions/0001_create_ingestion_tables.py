"""create ingestion tables

Revision ID: 0001_create_ingestion_tables
Revises: 
Create Date: 2026-02-01
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_create_ingestion_tables"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "raw_events",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("agent_id", sa.String(length=64), nullable=False),
        sa.Column("host_id", sa.String(length=128), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("sensor_version", sa.String(length=32), nullable=False),
        sa.Column("actor_user", sa.String(length=255), nullable=True),
        sa.Column("correlation_key", sa.String(length=255), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("ingestion_status", sa.String(length=32), server_default="accepted", nullable=False),
        sa.UniqueConstraint("event_id", name="uq_raw_events_event_id"),
    )

    op.create_index("ix_raw_events_tenant_id", "raw_events", ["tenant_id"], unique=False)
    op.create_index("ix_raw_events_category", "raw_events", ["category"], unique=False)
    op.create_index("ix_raw_events_occurred_at", "raw_events", ["occurred_at"], unique=False)

    op.create_table(
        "ingest_audit",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("raw_event_id", sa.BigInteger(), nullable=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("source_ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("auth_mechanism", sa.String(length=64), server_default="bearer_shared_token", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["raw_event_id"],
            ["raw_events.id"],
            name="fk_ingest_audit_raw_event_id_raw_events",
            ondelete="SET NULL",
        ),
    )

    op.create_index("ix_ingest_audit_event_id", "ingest_audit", ["event_id"], unique=False)
    op.create_index("ix_ingest_audit_request_id", "ingest_audit", ["request_id"], unique=False)
    op.create_index("ix_ingest_audit_decision", "ingest_audit", ["decision"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ingest_audit_decision", table_name="ingest_audit")
    op.drop_index("ix_ingest_audit_request_id", table_name="ingest_audit")
    op.drop_index("ix_ingest_audit_event_id", table_name="ingest_audit")
    op.drop_table("ingest_audit")

    op.drop_index("ix_raw_events_occurred_at", table_name="raw_events")
    op.drop_index("ix_raw_events_category", table_name="raw_events")
    op.drop_index("ix_raw_events_tenant_id", table_name="raw_events")
    op.drop_table("raw_events")