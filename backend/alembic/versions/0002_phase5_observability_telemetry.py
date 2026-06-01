"""phase 5 observability telemetry

Revision ID: 0002_phase5
Revises: 0001_phase4
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa

import app.models  # noqa: F401
from app.core.database import Base


revision = "0002_phase5"
down_revision = "0001_phase4"
branch_labels = None
depends_on = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    tables = _tables()
    for table_name in (
        "traces",
        "infrastructure_events",
        "log_entries",
        "metrics",
        "telemetry_sources",
    ):
        if table_name in tables:
            op.drop_table(table_name)
