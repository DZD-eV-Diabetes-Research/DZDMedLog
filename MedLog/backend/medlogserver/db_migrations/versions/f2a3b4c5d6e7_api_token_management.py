"""Schema for the user managed API tokens (issue #198).

Introduces:
- user_auth.api_token_name (nullable String; the name a user gives an API token created via
  the token management endpoints, so the token can be recognised in the token overview)
- user_auth.api_token_last_used_at (nullable DateTime; shown in the token overview)
- a unique index on user_auth.api_token_id. Tokens are looked up by this id on every API
  request. Existing ids are 96 bit random values, NULL (passwords, OIDC logins) is allowed
  multiple times on both dialects.
- user.last_oidc_login_at (nullable DateTime; managed tokens of OIDC users pause when the
  last OIDC login is older than API_TOKEN_MANAGEMENT_OIDC_LOGIN_MAX_AGE_DAYS)

Existing rows keep NULL. Users who logged in via OIDC before this migration get a value on
their next OIDC login, until then their managed tokens are not paused (they can not have
any, the token management did not exist before).

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-09-16 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, Sequence[str], None] = "e1f2a3b4c5d6"
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

    op.add_column(
        "user_auth",
        sa.Column("api_token_name", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "user_auth",
        sa.Column("api_token_last_used_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "user",
        sa.Column("last_oidc_login_at", sa.DateTime(), nullable=True),
    )

    # Plain CREATE/DROP INDEX works on both dialects, no batch mode needed.
    token_id_index = _existing_index("user_auth", "ix_user_auth_api_token_id")
    if token_id_index is not None and not token_id_index["unique"]:
        op.drop_index("ix_user_auth_api_token_id", table_name="user_auth")
        token_id_index = None
    if token_id_index is None:
        op.create_index(
            "ix_user_auth_api_token_id", "user_auth", ["api_token_id"], unique=True
        )


def downgrade():
    raise NotImplementedError(f"DZDMedLog does not support downgrading the database")
