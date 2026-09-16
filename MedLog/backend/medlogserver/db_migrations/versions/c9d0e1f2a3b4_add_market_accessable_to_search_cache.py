"""Add market_accessable to drug_search_generic_sql_cache

MMI Pharmindex keeps packages the supplier no longer delivers in its live
catalog without an OFFMARKETDATE, and marks them only through the sales status
attribute. Filtering on market_exit_date alone therefore let ~26k "Außer
Vertrieb" packages pass as still on the market (see GitHub issue #360).

The column is filled by the index build, not by the drug import, so no
re-import is needed. Existing rows stay NULL until the next index rebuild,
which the monthly drug data update triggers on its own. NULL reads as
"accessible", so the filter behaves exactly as before until then.

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-09-02 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = "b8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.add_column(
            "drug_search_generic_sql_cache",
            sa.Column("market_accessable", sa.Boolean(), nullable=True),
        )
    elif dialect == "sqlite":
        with op.batch_alter_table("drug_search_generic_sql_cache") as batch_op:
            batch_op.add_column(
                sa.Column("market_accessable", sa.Boolean(), nullable=True)
            )


def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.drop_column("drug_search_generic_sql_cache", "market_accessable")
    elif dialect == "sqlite":
        with op.batch_alter_table("drug_search_generic_sql_cache") as batch_op:
            batch_op.drop_column("market_accessable")
