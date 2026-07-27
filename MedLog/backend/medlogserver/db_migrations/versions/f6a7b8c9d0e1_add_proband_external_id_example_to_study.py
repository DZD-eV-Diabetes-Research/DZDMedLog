"""Add optional positive-example column for proband external IDs to study.

Introduces:
- proband_external_id_example (nullable String; a positive example such as 'AAA1111'
  the frontend can show proactively next to the proband-ID input)

Purely informational — it is not validated against proband_external_id_pattern. Follows
the nullable-string column style of proband_external_id_pattern from revision e5f6a7b8c9d0.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-27 09:57:51.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "study",
        sa.Column("proband_external_id_example", sa.String(length=1024), nullable=True),
    )


def downgrade():
    op.drop_column("study", "proband_external_id_example")
