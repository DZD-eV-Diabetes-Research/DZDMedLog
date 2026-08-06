"""Shared helper to build a proband-external-ID WHERE clause that honors a study's
normalization rule.

Used by the interview, intake and event CRUDs so that all proband lookups fold case
(or not) consistently per study. Existing (un-normalized) rows are matched by applying
the same SQL function to the stored column, so no data rewrite is required.
"""

from typing import Optional

from sqlalchemy import func

from medlogserver.model.study import (
    ProbandExternalIdNormalization,
    normalize_proband_external_id,
)


def build_proband_external_id_filter(
    column,
    value: str,
    normalization: Optional[ProbandExternalIdNormalization],
):
    """Return a SQLAlchemy boolean expression matching ``column`` against ``value``
    under the given per-study normalization.

    - NONE -> exact match (case-sensitive)
    - UPPERCASE -> case-insensitive via ``UPPER()`` on both sides
    - LOWERCASE -> case-insensitive via ``LOWER()`` on both sides
    """
    normalized_value = normalize_proband_external_id(value, normalization)
    if normalization == ProbandExternalIdNormalization.UPPERCASE:
        return func.upper(column) == normalized_value
    if normalization == ProbandExternalIdNormalization.LOWERCASE:
        return func.lower(column) == normalized_value
    return column == normalized_value
