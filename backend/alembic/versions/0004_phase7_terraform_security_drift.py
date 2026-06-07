"""phase 7 terraform security drift

Revision ID: 0004_phase7
Revises: 0003_phase6
Create Date: 2026-06-07
"""

import sqlalchemy as sa
from alembic import op

import app.models  # noqa: F401
from app.core.database import Base


revision = "0004_phase7"
down_revision = "0003_phase6"
branch_labels = None
depends_on = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _columns(table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())

    if "terraform_scans" in _tables():
        columns = _columns("terraform_scans")
        with op.batch_alter_table("terraform_scans") as batch:
            if "workspace_id" not in columns:
                batch.add_column(sa.Column("workspace_id", sa.String(length=36), nullable=True))
                batch.create_index("ix_terraform_scans_workspace_id", ["workspace_id"])
            if "source_type" not in columns:
                batch.add_column(sa.Column("source_type", sa.String(length=50), nullable=True))
            if "policy_violation_count" not in columns:
                batch.add_column(sa.Column("policy_violation_count", sa.Integer(), nullable=True))
            if "drift_count" not in columns:
                batch.add_column(sa.Column("drift_count", sa.Integer(), nullable=True))


def downgrade() -> None:
    tables = _tables()
    for table_name in (
        "terraform_policy_violations",
        "terraform_drift",
        "terraform_findings",
        "terraform_resources",
        "terraform_workspaces",
    ):
        if table_name in tables:
            op.drop_table(table_name)
