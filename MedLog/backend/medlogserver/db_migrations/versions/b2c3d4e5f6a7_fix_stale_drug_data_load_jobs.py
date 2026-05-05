"""Fix stale DRUG_DATA_LOAD jobs stuck in RUNNING state

Jobs that were interrupted by a container restart mid index-build were left with
run_started_at set but run_finished_at and last_error both NULL (RUNNING forever).
With the index rebuild now decoupled from the load job (issue #285) these jobs
will never self-resolve, so we close them here as FAILED.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-05 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STALE_ERROR_MSG = (
    "Job was interrupted before completion (container restart or process crash). "
    "Closed by migration b2c3d4e5f6a7 (issue #285). "
    "The search index rebuild is now handled independently and will recover automatically."
)


def upgrade():
    # tags is stored as CSV text; jobs created after the appVersion tag was
    # introduced will contain the substring "appVersion:" in that column.
    # We only close jobs that pre-date the fix (no version tag) to avoid
    # accidentally killing jobs from a version that already has the fix.
    op.execute(
        sa.text(
            "UPDATE worker_job "
            "SET run_finished_at = CURRENT_TIMESTAMP, last_error = :msg "
            "WHERE task_name = 'DRUG_DATA_LOAD' "
            "  AND run_started_at IS NOT NULL "
            "  AND run_finished_at IS NULL "
            "  AND last_error IS NULL "
            "  AND (tags NOT LIKE '%appVersion:%' OR tags IS NULL)"
        ).bindparams(msg=_STALE_ERROR_MSG)
    )


def downgrade():
    # Cannot distinguish these rows from genuinely failed jobs after the fact.
    pass
