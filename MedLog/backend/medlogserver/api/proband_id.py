"""Proband-external-ID validation helpers for the API layer.

Single source of truth for turning a study's configured regex pattern + normalization
into an accept/reject decision. Shared by the interview write path and the validation
endpoint so the logic is never duplicated.
"""

import re
from typing import Optional, Tuple

from fastapi import HTTPException, status

from medlogserver.model._base_model import MedLogBaseModel
from medlogserver.model.study import (
    Study,
    ProbandExternalIdNormalization,
    normalize_proband_external_id,
)

GENERIC_PROBAND_ID_ERROR_TEXT = (
    "The entered proband ID does not match the required format for this study."
)


class ProbandIdValidationResult(MedLogBaseModel):
    valid: bool
    normalized_proband_external_id: str
    error_text: Optional[str] = None


def check_proband_id(
    study: Study,
    raw_proband_external_id: str,
) -> Tuple[bool, str, Optional[str]]:
    """Normalize + validate without raising.

    Returns ``(valid, normalized_value, error_text_if_invalid)``. Fails closed if the
    stored pattern no longer compiles (valid=False with an admin-facing error text).
    """
    normalized = normalize_proband_external_id(
        raw_proband_external_id, study.proband_external_id_normalization
    )
    pattern = study.proband_external_id_pattern
    if pattern in (None, ""):
        return True, normalized, None

    try:
        matches = re.fullmatch(pattern, normalized) is not None
    except re.error:
        # Pattern was valid when stored but no longer compiles -> fail closed.
        return (
            False,
            normalized,
            "The proband ID validation pattern configured for this study is no longer "
            "a valid regular expression and must be fixed by a study administrator.",
        )
    if not matches:
        error_text = (
            study.proband_external_id_pattern_error_text
            or GENERIC_PROBAND_ID_ERROR_TEXT
        )
        return False, normalized, error_text
    return True, normalized, None


def assert_valid_proband_id_pattern(pattern: Optional[str]) -> None:
    """Ensure a study's proband-ID regex compiles. Raise HTTP 422 otherwise.

    Called when a study is created/updated so an invalid pattern can never be stored
    and later break interview creation. Also backs the frontend 'test pattern' field.
    """
    if pattern in (None, ""):
        return
    try:
        re.compile(pattern)
    except re.error as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid proband ID validation pattern (regular expression): {e}",
        )


def normalize_and_validate_proband_id(
    study: Study,
    raw_proband_external_id: str,
) -> str:
    """Normalize a proband ID per the study rule, then validate it against the study pattern.

    Returns the normalized (canonical) value to be stored/looked up.
    Raises HTTP 422 with the study's configured (or a generic) error text on mismatch.

    Fails closed: if a stored pattern can no longer be compiled (e.g. after a runtime
    upgrade), the ID is rejected rather than silently accepted.
    """
    valid, normalized, error_text = check_proband_id(study, raw_proband_external_id)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=error_text,
        )
    return normalized
