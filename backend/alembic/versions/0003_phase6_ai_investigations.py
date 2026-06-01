"""phase 6 ai investigations

Revision ID: 0003_phase6
Revises: 0002_phase5
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa

import app.models  # noqa: F401
from app.core.database import Base


revision = "0003_phase6"
down_revision = "0002_phase5"
branch_labels = None
depends_on = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    tables = _tables()
    for table_name in ("investigation_evidence", "investigations"):
        if table_name in tables:
            op.drop_table(table_name)
