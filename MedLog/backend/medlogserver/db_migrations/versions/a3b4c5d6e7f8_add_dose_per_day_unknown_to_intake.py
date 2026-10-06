"""Add intake.dose_per_day_unknown and migrate the unknown-dose placeholders

Interviewers recorded an unknown daily dose ("Dosis pro Tag der Einnahme") as
the placeholder 9999, and the API documented 0 as "the daily dose is unknown"
(review of issue #338). Both placeholders are treated the same.

This adds the boolean column intake.dose_per_day_unknown (NOT NULL, default
false) and converts the placeholders 9999 and 0, depending on the intake mode:

- regular intake or intake mode not set: dose_per_day NULL,
  dose_per_day_unknown true
- as-needed intake: dose_per_day NULL, dose_per_day_unknown stays false. A
  daily dose does not apply to as-needed intakes (the web client disables the
  field and sends its default 0), so there is nothing to mark as unknown.

See: https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues/384

Revision ID: a3b4c5d6e7f8
Revises: f2a3b4c5d6e7
Create Date: 2026-10-05 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a3b4c5d6e7f8"
down_revision: Union[str, Sequence[str], None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UNKNOWN_DOSE_PLACEHOLDERS = (9999, 0)

# Stored value of the `intakeregularorasneededanswers` enum (the member name).
ASNEEDED = "ASNEEDED"


def upgrade():
    dialect = op.get_bind().dialect.name
    if dialect not in ("postgresql", "sqlite"):
        raise NotImplementedError(
            f"DZDMedLog only supports Postgres (and SQlite for local development). Please use another database as '{dialect}'"
        )

    # The server default fills the existing rows. A plain ADD COLUMN works on
    # both dialects, SQLite accepts NOT NULL here because a default is given.
    op.add_column(
        "intake",
        sa.Column(
            "dose_per_day_unknown",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    intake = sa.table(
        "intake",
        sa.column("dose_per_day", sa.Numeric()),
        sa.column("dose_per_day_unknown", sa.Boolean()),
        sa.column("intake_regular_or_as_needed", sa.String()),
    )
    # Compared as text: on Postgres the column is a native enum type, which has
    # no comparison operator against a VARCHAR parameter.
    mode = sa.cast(intake.c.intake_regular_or_as_needed, sa.String())
    placeholder = intake.c.dose_per_day.in_(UNKNOWN_DOSE_PLACEHOLDERS)

    op.execute(
        intake.update()
        .where(placeholder, sa.or_(mode.is_(None), mode != ASNEEDED))
        .values(dose_per_day=None, dose_per_day_unknown=True)
    )
    op.execute(
        intake.update()
        .where(placeholder, mode == ASNEEDED)
        .values(dose_per_day=None)
    )


def downgrade():
    raise NotImplementedError(f"DZDMedLog does not support downgrading the database")
