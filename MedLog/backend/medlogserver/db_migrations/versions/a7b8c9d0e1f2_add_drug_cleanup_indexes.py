"""Add the indexes the obsolete-drug cleanup needs to run in reasonable time.

The DrugDataSetCleaner deletes obsolete drug rows in batches. Three unindexed
columns made that pathologically slow (see issue #331):

- `drug_code.drug_id`: the primary key is (id, drug_id, code_system_id), so
  `id` is leftmost and the PK index cannot serve drug_id lookups. Every deleted
  drug therefore triggered a full scan of drug_code, either through the
  ON DELETE CASCADE foreign key or through the cleanup's own child deletes.
- `intake.drug_id`: unindexed foreign key, so PostgreSQL runs a sequential
  referential-integrity check per deleted drug row, and the cleanup's
  anti-join against intake has no index to work with either.
- `drug.source_dataset_id`: unindexed, so selecting the next batch full-scans
  the whole drug table.

Measured on PostgreSQL 15 with 300k drugs / 900k drug codes / 1.8M attr rows:
deleting one batch of 2000 drugs took 117 s before and 0.09 s after.

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-08-19 10:12:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (index name, table, column)
_INDEXES = [
    ("ix_drug_code_drug_id", "drug_code", "drug_id"),
    ("ix_intake_drug_id", "intake", "drug_id"),
    ("ix_drug_source_dataset_id", "drug", "source_dataset_id"),
]


def _existing_index_names(table: str) -> set:
    inspector = sa.inspect(op.get_bind())
    return {index["name"] for index in inspector.get_indexes(table)}


def upgrade():
    for index_name, table, column in _INDEXES:
        # Instances that were created from the current models rather than migrated
        # may already carry these indexes. Creating them twice is an error on both
        # SQLite and PostgreSQL, so check first.
        if index_name in _existing_index_names(table):
            continue
        op.create_index(index_name, table, [column], unique=False)


def downgrade():
    for index_name, table, _ in reversed(_INDEXES):
        if index_name not in _existing_index_names(table):
            continue
        op.drop_index(index_name, table_name=table)
