"""create normalized events table

Revision ID: 0002_create_normalized_events_table
Revises: 0001_create_ingestion_tables
Create Date: 2026-04-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_norm_events"
down_revision: str | None = "0001_create_ingestion_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "normalized_events",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("raw_event_id", sa.BigInteger(), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("normalization_version", sa.String(length=16), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("event_action", sa.String(length=64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("normalized_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("agent_id", sa.String(length=64), nullable=False),
        sa.Column("host_id", sa.String(length=128), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("sensor_version", sa.String(length=32), nullable=False),
        sa.Column("actor_user", sa.String(length=255), nullable=True),
        sa.Column("correlation_key", sa.String(length=255), nullable=True),
        sa.Column("process_name", sa.String(length=255), nullable=True),
        sa.Column("process_pid", sa.Integer(), nullable=True),
        sa.Column("file_path", sa.String(length=1024), nullable=True),
        sa.Column("destination_ip", sa.String(length=64), nullable=True),
        sa.Column("destination_port", sa.Integer(), nullable=True),
        sa.Column("auth_result", sa.String(length=64), nullable=True),
        sa.Column("normalized_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["raw_event_id"],
            ["raw_events.id"],
            name="fk_normalized_events_raw_event_id_raw_events",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("raw_event_id", name="uq_normalized_events_raw_event_id"),
    )

    op.create_index("ix_normalized_events_tenant_id", "normalized_events", ["tenant_id"], unique=False)
    op.create_index("ix_normalized_events_category", "normalized_events", ["category"], unique=False)
    op.create_index("ix_normalized_events_occurred_at", "normalized_events", ["occurred_at"], unique=False)
    op.create_index("ix_normalized_events_event_action", "normalized_events", ["event_action"], unique=False)
    op.create_index("ix_normalized_events_hostname", "normalized_events", ["hostname"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_normalized_events_hostname", table_name="normalized_events")
    op.drop_index("ix_normalized_events_event_action", table_name="normalized_events")
    op.drop_index("ix_normalized_events_occurred_at", table_name="normalized_events")
    op.drop_index("ix_normalized_events_category", table_name="normalized_events")
    op.drop_index("ix_normalized_events_tenant_id", table_name="normalized_events")
    op.drop_table("normalized_events")