"""create alerts tables

Revision ID: 0003_alerts
Revises: 0002_norm_events
Create Date: 2026-04-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_alerts"
down_revision: str | None = "0002_norm_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "alerts",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("alert_uid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("normalized_event_id", sa.BigInteger(), nullable=False),
        sa.Column("raw_event_id", sa.BigInteger(), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("rule_id", sa.String(length=64), nullable=False),
        sa.Column("rule_name", sa.String(length=255), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.String(length=1024), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="open", nullable=False),
        sa.Column("agent_id", sa.String(length=64), nullable=False),
        sa.Column("host_id", sa.String(length=128), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=False),
        sa.Column("actor_user", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["normalized_event_id"],
            ["normalized_events.id"],
            name="fk_alerts_normalized_event_id_normalized_events",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["raw_event_id"],
            ["raw_events.id"],
            name="fk_alerts_raw_event_id_raw_events",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("alert_uid", name="uq_alerts_alert_uid"),
        sa.UniqueConstraint("rule_id", "normalized_event_id", name="uq_alerts_rule_id_normalized_event_id"),
    )

    op.create_index("ix_alerts_tenant_id", "alerts", ["tenant_id"], unique=False)
    op.create_index("ix_alerts_rule_id", "alerts", ["rule_id"], unique=False)
    op.create_index("ix_alerts_severity", "alerts", ["severity"], unique=False)
    op.create_index("ix_alerts_status", "alerts", ["status"], unique=False)
    op.create_index("ix_alerts_hostname", "alerts", ["hostname"], unique=False)
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"], unique=False)

    op.create_table(
        "alert_evidence",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("alert_id", sa.BigInteger(), nullable=False),
        sa.Column("evidence_type", sa.String(length=64), nullable=False),
        sa.Column("evidence_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["alert_id"],
            ["alerts.id"],
            name="fk_alert_evidence_alert_id_alerts",
            ondelete="CASCADE",
        ),
    )

    op.create_index("ix_alert_evidence_alert_id", "alert_evidence", ["alert_id"], unique=False)
    op.create_index("ix_alert_evidence_evidence_type", "alert_evidence", ["evidence_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_alert_evidence_evidence_type", table_name="alert_evidence")
    op.drop_index("ix_alert_evidence_alert_id", table_name="alert_evidence")
    op.drop_table("alert_evidence")

    op.drop_index("ix_alerts_created_at", table_name="alerts")
    op.drop_index("ix_alerts_hostname", table_name="alerts")
    op.drop_index("ix_alerts_status", table_name="alerts")
    op.drop_index("ix_alerts_severity", table_name="alerts")
    op.drop_index("ix_alerts_rule_id", table_name="alerts")
    op.drop_index("ix_alerts_tenant_id", table_name="alerts")
    op.drop_table("alerts")