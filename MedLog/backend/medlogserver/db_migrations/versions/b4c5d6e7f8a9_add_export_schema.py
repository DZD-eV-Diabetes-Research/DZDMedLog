"""Add export_schema table

Stores the schemas of the study export (JSON Schema for the JSON export,
Frictionless Table Schema for the CSV export). The API and the background
worker can run in different containers, so the worker writes the built
schemas into the database instead of a file.

A schema depends on the MedLog version (fixed export columns) and the drug
dataset version (reference list values), so these two and the format are the
primary key. The table starts empty. On startup a build job is queued when no
schema exists for the running version, so no data migration is needed.

See: https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues/387

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f8
Create Date: 2026-10-07 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "b4c5d6e7f8a9"
down_revision: Union[str, Sequence[str], None] = "a3b4c5d6e7f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    dialect = op.get_bind().dialect.name
    if dialect not in ("postgresql", "sqlite"):
        raise NotImplementedError(
            f"DZDMedLog only supports Postgres (and SQlite for local development). Please use another database as '{dialect}'"
        )

    op.create_table(
        "export_schema",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column(
            "medlog_version", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column(
            "drug_dataset_version",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=False,
        ),
        sa.Column("format", sa.String(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("medlog_version", "drug_dataset_version", "format"),
        comment="Schemas of the study export, one per MedLog version, drug dataset version and format. Built by a worker job, can be deleted at any time (they are rebuilt on startup).",
    )


def downgrade():
    raise NotImplementedError(f"DZDMedLog does not support downgrading the database")
