"""Allow fractional values for intake.dose_per_day

Users record half or quarter tablets ("Dosis pro Tag der Einnahme"), which the
integer column could not store. Widens the column to NUMERIC(6, 2), so values
such as 0.25, 0.2 or 1.25 are kept exactly. Existing integer values survive the
cast unchanged.

See: https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues/337

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-08-19 10:12:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, Sequence[str], None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PRECISION = 6
SCALE = 2


def upgrade():
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        op.alter_column(
            "intake",
            "dose_per_day",
            existing_type=sa.Integer(),
            type_=sa.Numeric(precision=PRECISION, scale=SCALE),
            existing_nullable=True,
            postgresql_using=f"dose_per_day::numeric({PRECISION},{SCALE})",
        )
    elif dialect == "sqlite":
        # No-op on purpose. SQLite is dynamically typed: an INTEGER-affinity
        # column already stores 0.25 as a REAL without truncation, and the ORM
        # reads it back through the Numeric type either way. Changing the
        # declared type would mean recreating the table via batch mode, which
        # would silently drop the enum CHECK constraints of this table, because
        # SQLAlchemy cannot reflect CHECK constraints on SQLite.
        pass
    else:
        raise NotImplementedError(
            f"DZDMedLog only supports Postgres (and SQlite for local development). Please use another database as '{dialect}'"
        )


def downgrade():
    raise NotImplementedError(
        "Downgrading would round fractional doses to whole doses and lose data."
    )
