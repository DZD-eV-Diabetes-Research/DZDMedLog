"""Automated migration: last hotfix for mmi drug updater 🤞

Revision ID: a60dae4c25ee
Revises: be5f522cc505
Create Date: 2026-02-25 08:41:26.365192
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a60dae4c25ee"
down_revision: Union[str, Sequence[str], None] = "be5f522cc505"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        # -------------------------
        # 1️⃣ Rename + convert columns to DATE
        # -------------------------
        op.execute("""
            ALTER TABLE intake
            RENAME COLUMN intake_start_time_utc TO intake_start_date
        """)
        op.execute("""
            ALTER TABLE intake
            ALTER COLUMN intake_start_date TYPE DATE
            USING intake_start_date::date
        """)

        op.execute("""
            ALTER TABLE intake
            RENAME COLUMN intake_end_time_utc TO intake_end_date
        """)
        op.execute("""
            ALTER TABLE intake
            ALTER COLUMN intake_end_date TYPE DATE
            USING intake_end_date::date
        """)

        # -------------------------
        # 2️⃣ Create enum types
        # -------------------------
        start_option_enum = sa.Enum(
            "UNKNOWN", "AT_LEAST_12_MONTHS", name="intakestartdateoption"
        )
        end_option_enum = sa.Enum("UNKNOWN", "ONGOING", name="intakeenddateoption")

        start_option_enum.create(bind, checkfirst=True)
        end_option_enum.create(bind, checkfirst=True)

        # -------------------------
        # 3️⃣ Add new option columns
        # -------------------------
        op.add_column(
            "intake",
            sa.Column(
                "intake_start_date_option",
                sa.Enum(
                    "UNKNOWN",
                    "AT_LEAST_12_MONTHS",
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
                    "UNKNOWN",
                    "ONGOING",
                    name="intakeenddateoption",
                    create_type=False,
                ),
                nullable=True,
            ),
        )

        # -------------------------
        # 4️⃣ Backfill
        # -------------------------
        op.execute("""
            UPDATE intake
            SET intake_start_date_option = 'UNKNOWN'
            WHERE intake_start_date IS NULL
              AND intake_start_date_option IS NULL
        """)

        # -------------------------
        # 5️⃣ Constraints
        # -------------------------
        op.execute("""
            ALTER TABLE intake ADD CONSTRAINT chk_intake_start_date CHECK (
                (intake_start_date IS NOT NULL AND intake_start_date_option IS NULL)
                OR
                (intake_start_date IS NULL AND intake_start_date_option IS NOT NULL)
            )
        """)

        op.execute("""
            ALTER TABLE intake ADD CONSTRAINT chk_intake_end_date CHECK (
                NOT (intake_end_date IS NOT NULL AND intake_end_date_option IS NOT NULL)
            )
        """)

    elif dialect == "sqlite":
        # SQLite requires batch mode for column rename/type changes
        with op.batch_alter_table("intake") as batch_op:
            batch_op.alter_column(
                "intake_start_time_utc",
                new_column_name="intake_start_date",
                existing_type=sa.DateTime(),
                type_=sa.Date(),
            )
            batch_op.alter_column(
                "intake_end_time_utc",
                new_column_name="intake_end_date",
                existing_type=sa.DateTime(),
                type_=sa.Date(),
            )

            batch_op.add_column(
                sa.Column("intake_start_date_option", sa.String(), nullable=True)
            )
            batch_op.add_column(
                sa.Column("intake_end_date_option", sa.String(), nullable=True)
            )

        op.execute("""
            UPDATE intake
            SET intake_start_date_option = 'UNKNOWN'
            WHERE intake_start_date IS NULL
              AND intake_start_date_option IS NULL
        """)

        # SQLite cannot add CHECK constraints via ALTER TABLE.
        # Enforced at application layer.

    else:
        raise NotImplementedError(
            f"DZDMedLog only supports Postgres (and SQLite for local development). "
            f"'{dialect}' is not supported."
        )


def downgrade():
    raise NotImplementedError("DZDMedLog does not support downgrading the database")
