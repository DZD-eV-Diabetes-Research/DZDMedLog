"""Proband-external-ID validation helpers for the API layer.

Single source of truth for turning a (regex pattern + normalization) pair into an
accept/reject decision. Shared by three callers so the logic is never duplicated:

- the interview write path (authoritative, raises HTTP 422 on mismatch),
- the saved-study ``/validate`` endpoint (checks against a stored study), and
- the stateless ``/validate-pattern`` endpoint (checks against an *unsaved* pattern the
  study-config UI is still editing — never touches the DB).

All three go through :func:`core_check_proband_id`, which normalizes then applies
``re.fullmatch`` (anchored: the whole string must match, ``^``/``$`` are implied).
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

# Admin-facing text used when a *stored* study pattern can no longer be compiled. Kept
# separate from the raw-regex-error text of the stateless test endpoint: a study
# interviewer must not be shown the internal regex error, only told to contact an admin.
STORED_PATTERN_BROKEN_ERROR_TEXT = (
    "The proband ID validation pattern configured for this study is no longer "
    "a valid regular expression and must be fixed by a study administrator."
)


class ProbandIdCheckResult(MedLogBaseModel):
    """Full structured outcome of a normalize+validate check (internal, superset).

    ``pattern_compiles`` is ``True`` when there is no pattern at all (nothing to break).
    """

    valid: bool
    normalized: str
    error_text: Optional[str] = None
    pattern_compiles: bool = True


class ProbandIdValidationResult(MedLogBaseModel):
    """Response model of the saved-study ``/validate`` endpoint.

    ``normalized_proband_external_id`` is always the value the backend actually tried
    (e.g. it uppercased ``aaa1111`` to ``AAA1111``) so a rejecting frontend can show the
    user exactly what was checked. ``proband_external_id_example`` mirrors the study's
    optional positive example for convenient display.
    """

    valid: bool
    normalized_proband_external_id: str
    error_text: Optional[str] = None
    pattern_compiles: bool = True
    proband_external_id_example: Optional[str] = None


class ProbandIdPatternTestResult(MedLogBaseModel):
    """Response model of the stateless ``/validate-pattern`` endpoint.

    Lets the study-config UI offer a live 'test this pattern' field against an unsaved
    ``pattern`` + ``normalization`` before the study is saved. ``pattern_compiles`` is
    ``False`` (with ``valid=False``) when the entered regex does not compile.
    """

    valid: bool
    normalized_sample: str
    error_text: Optional[str] = None
    pattern_compiles: bool


def core_check_proband_id(
    pattern: Optional[str],
    normalization: Optional[ProbandExternalIdNormalization],
    configured_error_text: Optional[str],
    raw_proband_external_id: str,
) -> ProbandIdCheckResult:
    """Normalize + validate a raw proband ID against a pattern, without raising or DB access.

    This is the single shared core. ``pattern`` of ``None``/``""`` accepts anything.
    Uses ``re.fullmatch`` so the *entire* normalized string must match (``^``/``$`` are
    implied even if the stored pattern omits them).
    """
    normalized = normalize_proband_external_id(raw_proband_external_id, normalization)
    if pattern in (None, ""):
        return ProbandIdCheckResult(
            valid=True, normalized=normalized, error_text=None, pattern_compiles=True
        )
    try:
        compiled = re.compile(pattern)
    except re.error as e:
        return ProbandIdCheckResult(
            valid=False,
            normalized=normalized,
            error_text=f"Invalid proband ID validation pattern (regular expression): {e}",
            pattern_compiles=False,
        )
    # NOTE (issue #318, item 6): re.fullmatch has no timeout, so a pathological pattern
    # could backtrack catastrophically. The `regex` third-party module (which supports
    # timeout=) is not a dependency and we deliberately do not add one just for this. The
    # current mitigation is the 1024-char length cap on both the pattern and the proband
    # ID (see Study.proband_external_id_pattern), which bounds the input size.
    if compiled.fullmatch(normalized) is None:
        return ProbandIdCheckResult(
            valid=False,
            normalized=normalized,
            error_text=configured_error_text or GENERIC_PROBAND_ID_ERROR_TEXT,
            pattern_compiles=True,
        )
    return ProbandIdCheckResult(
        valid=True, normalized=normalized, error_text=None, pattern_compiles=True
    )


def check_proband_id(
    study: Study,
    raw_proband_external_id: str,
) -> Tuple[bool, str, Optional[str]]:
    """Normalize + validate against a *saved* study without raising.

    Returns ``(valid, normalized_value, error_text_if_invalid)``. Fails closed if the
    stored pattern no longer compiles (valid=False with an admin-facing error text — the
    raw regex error is never surfaced to interviewers).
    """
    result = core_check_proband_id(
        study.proband_external_id_pattern,
        study.proband_external_id_normalization,
        study.proband_external_id_pattern_error_text,
        raw_proband_external_id,
    )
    if not result.pattern_compiles:
        # Pattern was valid when stored but no longer compiles -> fail closed.
        return False, result.normalized, STORED_PATTERN_BROKEN_ERROR_TEXT
    return result.valid, result.normalized, result.error_text


def build_proband_id_rejection_detail(
    message: str,
    normalized_proband_external_id: str,
) -> dict:
    """Shape a structured 422 ``detail`` for a rejected proband ID.

    Contract note (issue #318, item 3): ``detail`` is an object, not a bare string, so the
    frontend can surface *both* the human message and the exact normalized value the
    backend tried (e.g. it uppercased ``aaa1111`` to ``AAA1111`` and that still did not
    match). ``detail.message`` carries the human text previous string-only clients read.
    """
    return {
        "message": message,
        "normalized_proband_external_id": normalized_proband_external_id,
    }


def assert_valid_proband_id_pattern(pattern: Optional[str]) -> None:
    """Ensure a study's proband-ID regex compiles. Raise HTTP 422 otherwise.

    Called when a study is created/updated so an invalid pattern can never be stored
    and later break interview creation.
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
    Raises HTTP 422 on mismatch with a *structured* detail (message + the normalized value
    that was actually tried); see :func:`build_proband_id_rejection_detail`.

    Fails closed: if a stored pattern can no longer be compiled (e.g. after a runtime
    upgrade), the ID is rejected rather than silently accepted.
    """
    valid, normalized, error_text = check_proband_id(study, raw_proband_external_id)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=build_proband_id_rejection_detail(error_text, normalized),
        )
    return normalized
