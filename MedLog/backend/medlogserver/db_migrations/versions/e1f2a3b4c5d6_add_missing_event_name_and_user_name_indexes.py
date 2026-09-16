"""Add missing indexes on event.name and user.user_name

The models declare `index=True` on `event.name` and `user.user_name`, but the
baseline migration (654143bb0e87) never created these indexes. Databases created
through the migrations therefore lack them, and `SQLModel.metadata.create_all`
at startup does not add indexes to tables that already exist.

Databases that existed before the baseline reset were created by `create_all`
and stamped, so they may already have both indexes, `ix_user_user_name` as a
UNIQUE index. The model now declares `user.user_name` as a non-unique index
(a unique one could fail the upgrade on existing duplicates; `UserCRUD.create`
checks for an existing user_name instead). This migration therefore:

* creates each index if it is missing,
* replaces an existing unique `ix_user_user_name` with a non-unique one, so all
  databases end up with the same schema.

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-09-16 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, Sequence[str], None] = "d0e1f2a3b4c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _existing_index(table: str, index_name: str) -> dict | None:
    inspector = sa.inspect(op.get_bind())
    for index in inspector.get_indexes(table):
        if index["name"] == index_name:
            return index
    return None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect not in ("postgresql", "sqlite"):
        raise NotImplementedError(
            f"DZDMedLog only supports Postgres (and SQlite for local development). Please use another database as '{dialect}'"
        )

    # Plain CREATE/DROP INDEX works on both dialects, no batch mode needed.
    if _existing_index("event", "ix_event_name") is None:
        op.create_index("ix_event_name", "event", ["name"], unique=False)

    user_name_index = _existing_index("user", "ix_user_user_name")
    if user_name_index is not None and user_name_index["unique"]:
        op.drop_index("ix_user_user_name", table_name="user")
        user_name_index = None
    if user_name_index is None:
        op.create_index("ix_user_user_name", "user", ["user_name"], unique=False)


def downgrade():
    raise NotImplementedError(f"DZDMedLog does not support downgrading the database")
