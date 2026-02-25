"""Automated migration: Hotfix for obsolete passlib

Revision ID: 328eaf68f1a1
Revises: e1d280620446
Create Date: 2025-11-21 16:34:02.060238

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
import medlogserver.model._utils


# revision identifiers, used by Alembic.
revision: str = "328eaf68f1a1"
down_revision: Union[str, Sequence[str], None] = "e1d280620446"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        # Create the enum types first (Postgres requires explicit type objects)
        start_option_enum = sa.Enum(
            "unknown", "at_least_12_months", name="intakestartdateoption"
        )
        end_option_enum = sa.Enum("unknown", "ongoing", name="intakeenddateoption")
        start_option_enum.create(bind, checkfirst=True)
        end_option_enum.create(bind, checkfirst=True)

        op.add_column(
            "intake",
            sa.Column(
                "intake_start_date_option",
                sa.Enum(
                    "unknown",
                    "at_least_12_months",
                    name="intakestartdateoption",
                    create_type=False,
                ),
                nullable=True,
            ),
        )
        op.add_column(
            "intake",
            sa.Column(
                "intake_end_date_option",
                sa.Enum(
                    "unknown", "ongoing", name="intakeenddateoption", create_type=False
                ),
                nullable=True,
            ),
        )

        # Backfill: any row missing a start date gets 'unknown'
        op.execute("""
            UPDATE intake
            SET intake_start_date_option = 'unknown'
            WHERE intake_start_time_utc IS NULL
              AND intake_start_date_option IS NULL
        """)

        # Enforce XOR at DB level: exactly one of date/option must be set for start
        op.execute("""
            ALTER TABLE intake ADD CONSTRAINT chk_intake_start_date CHECK (
                (intake_start_time_utc IS NOT NULL AND intake_start_date_option IS NULL)
                OR
                (intake_start_time_utc IS NULL AND intake_start_date_option IS NOT NULL)
            )
        """)
        # Enforce mutual exclusivity for end date (both NULL is fine = no end info yet)
        op.execute("""
            ALTER TABLE intake ADD CONSTRAINT chk_intake_end_date CHECK (
                NOT (intake_end_time_utc IS NOT NULL AND intake_end_date_option IS NOT NULL)
            )
        """)

    elif dialect == "sqlite":
        # SQLite has no native enum type — store as plain VARCHAR.
        # Pydantic/SQLModel validation enforces allowed values at the app layer.
        with op.batch_alter_table("intake") as batch_op:
            batch_op.add_column(
                sa.Column("intake_start_date_option", sa.String(), nullable=True)
            )
            batch_op.add_column(
                sa.Column("intake_end_date_option", sa.String(), nullable=True)
            )

        # Backfill runs outside batch (needs the columns to exist first)
        op.execute("""
            UPDATE intake
            SET intake_start_date_option = 'unknown'
            WHERE intake_start_time_utc IS NULL
              AND intake_start_date_option IS NULL
        """)
        # Note: SQLite does not support CHECK constraints via ALTER TABLE;
        # the XOR logic is enforced exclusively at the application level.

    else:
        raise NotImplementedError(
            f"DZDMedLog only supports Postgres (and SQLite for local development). "
            f"'{dialect}' is not supported."
        )


def downgrade():
    raise NotImplementedError("DZDMedLog does not support downgrading the database")
