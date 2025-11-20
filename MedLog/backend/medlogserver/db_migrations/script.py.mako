"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
import medlogserver.model._utils
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, Sequence[str], None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}



def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        # --- PostgreSQL-specific upgrade ---
% if upgrades:
% for line in upgrades.splitlines():
        ${line}
% endfor
% else:
        pass
% endif
    elif dialect == "sqlite":
        # --- SQLite-specific upgrade ---
% if upgrades:
% for line in upgrades.splitlines():
        ${line}
% endfor
% else:
        pass
% endif
    else:
        raise NotImplementedError(f"DZDMedLog only supports Postgres (and SQlite for local development). Please use another database as '{dialect}'") 


def downgrade():
        raise NotImplementedError(f"DZDMedLog does not support downgrading the database")