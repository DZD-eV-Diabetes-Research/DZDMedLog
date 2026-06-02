"""Add oidc_managed_permissions column to study_permission table.

Tracks which permission flags were granted by OIDC group mapping so that
manually-set flags are never revoked by OIDC on a subsequent login.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-02 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "study_permission",
        sa.Column(
            "oidc_managed_permissions",
            sa.JSON(),
            nullable=True,
        ),
    )
    # Backfill existing rows with an empty list so the application never sees NULL.
    op.execute(
        sa.text(
            "UPDATE study_permission SET oidc_managed_permissions = '[]' "
            "WHERE oidc_managed_permissions IS NULL"
        )
    )


def downgrade():
    op.drop_column("study_permission", "oidc_managed_permissions")
