"""Add index_build_started_at to drug_search_generic_sql_state

Fixes stale lock detection for index builds that are interrupted by container
restarts or process crashes (see GitHub issue #285).

Revision ID: a1b2c3d4e5f6
Revises: 654143bb0e87
Create Date: 2026-05-04 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "654143bb0e87"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.add_column(
            "drug_search_generic_sql_state",
            sa.Column("index_build_started_at", sa.DateTime(), nullable=True),
        )
        # If a build was stuck in-progress (e.g. from a pre-fix container restart),
        # clear the lock so the next run rebuilds cleanly.
        op.execute(
            sa.text(
                "UPDATE drug_search_generic_sql_state "
                "SET index_build_up_in_process = FALSE, index_build_started_at = NULL "
                "WHERE index_build_up_in_process = TRUE"
            )
        )
    elif dialect == "sqlite":
        with op.batch_alter_table("drug_search_generic_sql_state") as batch_op:
            batch_op.add_column(
                sa.Column("index_build_started_at", sa.DateTime(), nullable=True)
            )
        op.execute(
            sa.text(
                "UPDATE drug_search_generic_sql_state "
                "SET index_build_up_in_process = 0, index_build_started_at = NULL "
                "WHERE index_build_up_in_process = 1"
            )
        )


def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.drop_column("drug_search_generic_sql_state", "index_build_started_at")
    elif dialect == "sqlite":
        with op.batch_alter_table("drug_search_generic_sql_state") as batch_op:
            batch_op.drop_column("index_build_started_at")
