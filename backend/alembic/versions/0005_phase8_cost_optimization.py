"""phase 8 cost optimization

Revision ID: 0005_phase8
Revises: 0004_phase7
Create Date: 2026-06-07
"""

import sqlalchemy as sa
from alembic import op

import app.models  # noqa: F401
from app.core.database import Base


revision = "0005_phase8"
down_revision = "0004_phase7"
branch_labels = None
depends_on = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _columns(table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())

    if "cost_recommendations" in _tables():
        columns = _columns("cost_recommendations")
        with op.batch_alter_table("cost_recommendations") as batch:
            if "report_id" not in columns:
                batch.add_column(sa.Column("report_id", sa.String(length=36), nullable=True))
                batch.create_index("ix_cost_recommendations_report_id", ["report_id"])
            if "finding_id" not in columns:
                batch.add_column(sa.Column("finding_id", sa.String(length=36), nullable=True))
                batch.create_index("ix_cost_recommendations_finding_id", ["finding_id"])
            if "resource_type" not in columns:
                batch.add_column(sa.Column("resource_type", sa.String(length=100), nullable=True))
            if "resource_name" not in columns:
                batch.add_column(sa.Column("resource_name", sa.String(length=255), nullable=True))
            if "severity" not in columns:
                batch.add_column(sa.Column("severity", sa.String(length=30), nullable=True))
                batch.create_index("ix_cost_recommendations_severity", ["severity"])
            if "confidence_score" not in columns:
                batch.add_column(sa.Column("confidence_score", sa.Float(), nullable=True))
            if "recommendation" not in columns:
                batch.add_column(sa.Column("recommendation", sa.Text(), nullable=True))
            if "impact" not in columns:
                batch.add_column(sa.Column("impact", sa.Text(), nullable=True))
            if "evidence" not in columns:
                batch.add_column(sa.Column("evidence", sa.JSON(), nullable=True))


def downgrade() -> None:
    tables = _tables()
    for table_name in (
        "optimization_findings",
        "optimization_reports",
        "optimization_rules",
        "resource_utilization",
    ):
        if table_name in tables:
            op.drop_table(table_name)
