"""Add intake.intake_start_date_precision and intake.intake_end_date_precision

When only the month or the year of an intake start or end was known,
interviewers entered a placeholder day (usually the 15th), which is
indistinguishable from a real date. The new columns store the precision of each
date (`DAY`, `MONTH`, `YEAR`), a `MONTH` or `YEAR` date is stored as the first
day of its period.

Existing dates get `DAY`, they were entered as exact days. Rows with a date
option instead of a date keep NULL. No date is changed: existing placeholder
days stay as they are, cleaning them up is out of scope.

Like the other enum columns, the enum is stored by member NAME (native ENUM on
Postgres).

See: https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues/392

Revision ID: c5d6e7f8a9b0
Revises: b4c5d6e7f8a9
Create Date: 2026-10-09 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c5d6e7f8a9b0"
down_revision: Union[str, Sequence[str], None] = "b4c5d6e7f8a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_precision_enum = sa.Enum("DAY", "MONTH", "YEAR", name="intakedateprecision")

# Stored value of `IntakeDatePrecision.DAY` (the member name).
DAY = "DAY"


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect not in ("postgresql", "sqlite"):
        raise NotImplementedError(
            f"DZDMedLog only supports Postgres (and SQlite for local development). Please use another database as '{dialect}'"
        )

    # Create the native ENUM type on Postgres (no-op on SQLite). Both columns
    # share it.
    _precision_enum.create(bind, checkfirst=True)
    for date_column in ("intake_start_date", "intake_end_date"):
        op.add_column(
            "intake",
            sa.Column(f"{date_column}_precision", _precision_enum, nullable=True),
        )

    intake = sa.table(
        "intake",
        sa.column("intake_start_date", sa.Date()),
        sa.column("intake_end_date", sa.Date()),
        sa.column("intake_start_date_precision", _precision_enum),
        sa.column("intake_end_date_precision", _precision_enum),
    )
    op.execute(
        intake.update()
        .where(intake.c.intake_start_date.is_not(None))
        .values(intake_start_date_precision=DAY)
    )
    op.execute(
        intake.update()
        .where(intake.c.intake_end_date.is_not(None))
        .values(intake_end_date_precision=DAY)
    )


def downgrade():
    raise NotImplementedError(f"DZDMedLog does not support downgrading the database")
