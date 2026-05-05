"""Backfill closedByMigration tag on jobs already closed by b2c3d4e5f6a7

Migration b2c3d4e5f6a7 closed stale DRUG_DATA_LOAD jobs but was written before
the closedByMigration tag convention existed. Those jobs therefore lack the tag,
so the status endpoint cannot distinguish them from real failures.

This migration appends the tag to any pre-fix job (no appVersion: tag) that was
already closed (run_finished_at set, last_error set) but is missing the marker.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-05 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute(
        sa.text(
            "UPDATE worker_job "
            "SET tags = CASE WHEN tags IS NULL THEN 'closedByMigration' "
            "                ELSE tags || ',closedByMigration' END "
            "WHERE task_name = 'DRUG_DATA_LOAD' "
            "  AND run_finished_at IS NOT NULL "
            "  AND last_error IS NOT NULL "
            "  AND (tags NOT LIKE '%appVersion:%' OR tags IS NULL) "
            "  AND tags NOT LIKE '%closedByMigration%'"
        )
    )


def downgrade():
    pass
