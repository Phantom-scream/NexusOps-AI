"""enterprise audit events

Revision ID: 0006_audit
Revises: 0005_phase8
Create Date: 2026-06-07
"""

import sqlalchemy as sa
from alembic import op


revision = "0006_audit"
down_revision = "0005_phase8"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if _table_exists("audit_events"):
        return

    op.create_table(
        "audit_events",
        sa.Column("actor_id", sa.String(length=255), nullable=True),
        sa.Column("actor_email", sa.String(length=255), nullable=True),
        sa.Column("actor_role", sa.String(length=50), nullable=True),
        sa.Column("action", sa.String(length=150), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=True),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("request_id", sa.String(length=100), nullable=True),
        sa.Column("ip_address", sa.String(length=100), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "actor_id",
        "actor_email",
        "actor_role",
        "action",
        "resource_type",
        "resource_id",
        "status",
        "request_id",
        "timestamp",
    ):
        op.create_index(f"ix_audit_events_{column}", "audit_events", [column])


def downgrade() -> None:
    if not _table_exists("audit_events"):
        return

    op.drop_table("audit_events")
