"""phase 4 infrastructure topology

Revision ID: 0001_phase4
Revises:
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa

import app.models  # noqa: F401
from app.core.database import Base


revision = "0001_phase4"
down_revision = None
branch_labels = None
depends_on = None


def _columns(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    bind = op.get_bind()

    # This repository did not have earlier Alembic revisions, so create the
    # registered schema for fresh databases, then add Phase 4 columns for
    # databases that were previously bootstrapped via SQLAlchemy create_all.
    Base.metadata.create_all(bind=bind)

    cluster_columns = _columns("clusters")
    if "service_count" not in cluster_columns:
        op.add_column("clusters", sa.Column("service_count", sa.Integer(), nullable=True, server_default="0"))
    if "deployment_count" not in cluster_columns:
        op.add_column("clusters", sa.Column("deployment_count", sa.Integer(), nullable=True, server_default="0"))

    workload_columns = _columns("kubernetes_workloads")
    if "selector" not in workload_columns:
        op.add_column("kubernetes_workloads", sa.Column("selector", sa.JSON(), nullable=True))


def downgrade() -> None:
    tables = _tables()
    for table_name in ("kubernetes_services", "kubernetes_pods", "kubernetes_replicasets"):
        if table_name in tables:
            op.drop_table(table_name)

    workload_columns = _columns("kubernetes_workloads")
    if "selector" in workload_columns:
        op.drop_column("kubernetes_workloads", "selector")

    cluster_columns = _columns("clusters")
    if "deployment_count" in cluster_columns:
        op.drop_column("clusters", "deployment_count")
    if "service_count" in cluster_columns:
        op.drop_column("clusters", "service_count")
