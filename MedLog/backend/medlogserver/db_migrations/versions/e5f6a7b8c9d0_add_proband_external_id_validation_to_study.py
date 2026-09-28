"""Add per-study proband external ID validation + normalization columns to study.

Introduces:
- proband_external_id_pattern            (nullable regex; NULL/'' = accept anything)
- proband_external_id_pattern_error_text (nullable human-readable error text)
- proband_external_id_normalization       (enum NONE|UPPERCASE|LOWERCASE)

Also migrates the removed global PROBAND_IDS_CASE_SENSETIVE env var onto existing
studies so their proband-ID matching behavior is preserved:
- case-sensitive   (True)  -> 'NONE'      (exact match)
- case-insensitive (False) -> 'LOWERCASE' (former LOWER()-based matching)

Note: the enum is stored by member NAME (SQLAlchemy default, native ENUM on Postgres),
matching the convention of the other enum columns in this schema.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-27 00:00:00.000000

"""

import os
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_normalization_enum = sa.Enum(
    "NONE", "UPPERCASE", "LOWERCASE", name="probandexternalidnormalization"
)


def _old_case_sensitive_flag() -> bool:
    """Read the removed global PROBAND_IDS_CASE_SENSETIVE env var (default False)."""
    raw = os.getenv("PROBAND_IDS_CASE_SENSETIVE", "false")
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


def upgrade():
    bind = op.get_bind()
    # Create the native ENUM type on Postgres (no-op on SQLite).
    _normalization_enum.create(bind, checkfirst=True)

    op.add_column(
        "study",
        sa.Column("proband_external_id_pattern", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "study",
        sa.Column(
            "proband_external_id_pattern_error_text",
            sa.String(length=1024),
            nullable=True,
        ),
    )
    op.add_column(
        "study",
        sa.Column(
            "proband_external_id_normalization",
            _normalization_enum,
            nullable=False,
            server_default="NONE",
        ),
    )

    # Preserve the behavior of the former global flag for all existing studies.
    # Stored value is the enum member NAME.
    normalization = "NONE" if _old_case_sensitive_flag() else "LOWERCASE"
    op.execute(
        f"UPDATE study SET proband_external_id_normalization = '{normalization}'"
    )


def downgrade():
    op.drop_column("study", "proband_external_id_normalization")
    op.drop_column("study", "proband_external_id_pattern_error_text")
    op.drop_column("study", "proband_external_id_pattern")
    _normalization_enum.drop(op.get_bind(), checkfirst=True)
