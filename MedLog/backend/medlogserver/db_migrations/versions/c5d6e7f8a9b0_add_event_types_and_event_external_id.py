"""Add event types and an external ID to events

Introduces:
- event.external_id      (nullable String; free text to map events to IDs of
  external systems)
- event.event_type_mode  (nullable enum FIXED|DEFAULT|REQUIRED_CHOICE; how the
  event type of the interviews is set)
- event.event_type       (nullable String; the type for FIXED and DEFAULT)
- interview.event_type   (nullable String; the type the interview actually was)

All columns stay empty for existing rows: existing events do not track an event
type (mode NULL) until a study admin configures them, so existing events and
interviews stay valid. An interview without a type gets one on its next update
once its event is FIXED or DEFAULT.

Note: the enum is stored by member NAME (SQLAlchemy default, native ENUM on
Postgres), matching the convention of the other enum columns in this schema.

See: https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues/388

Revision ID: c5d6e7f8a9b0
Revises: b4c5d6e7f8a9
Create Date: 2026-10-08 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c5d6e7f8a9b0"
down_revision: Union[str, Sequence[str], None] = "b4c5d6e7f8a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_event_type_mode_enum = sa.Enum(
    "FIXED", "DEFAULT", "REQUIRED_CHOICE", name="eventtypemode"
)


def upgrade():
    # Create the native ENUM type on Postgres (no-op on SQLite).
    _event_type_mode_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "event",
        sa.Column("external_id", sa.String(), nullable=True),
    )
    op.add_column(
        "event",
        sa.Column("event_type_mode", _event_type_mode_enum, nullable=True),
    )
    op.add_column(
        "event",
        sa.Column("event_type", sa.String(), nullable=True),
    )
    op.add_column(
        "interview",
        sa.Column("event_type", sa.String(length=64), nullable=True),
    )


def downgrade():
    raise NotImplementedError(f"DZDMedLog does not support downgrading the database")
