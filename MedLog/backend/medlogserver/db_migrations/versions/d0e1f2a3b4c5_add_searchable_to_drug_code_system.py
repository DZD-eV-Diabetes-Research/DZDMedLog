"""Add searchable to drug_code_system

Drug attribute field definitions already had a `searchable` flag, drug code
systems did not, so every code of a drug ended up in the search index. Code
systems now declare it the same way (see GitHub issue #214).

Existing rows are set to TRUE, which is what the index build did for every code
until now. The importer overwrites the value with its code definition on the
next drug data import. The search index itself reads the flag from the importer
code, not from this column, so no index rebuild is needed.

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-09-16 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d0e1f2a3b4c5"
down_revision: Union[str, Sequence[str], None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.add_column(
            "drug_code_system",
            sa.Column(
                "searchable",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
        )
    elif dialect == "sqlite":
        with op.batch_alter_table("drug_code_system") as batch_op:
            batch_op.add_column(
                sa.Column(
                    "searchable",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.text("1"),
                )
            )


def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.drop_column("drug_code_system", "searchable")
    elif dialect == "sqlite":
        with op.batch_alter_table("drug_code_system") as batch_op:
            batch_op.drop_column("searchable")
