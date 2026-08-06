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

# Admin-facing text used when a *stored* study pattern is rejected as unsafe (see
# issue #318 item 6 / catastrophic backtracking). Fails closed the same way a broken
# pattern does: the interview is rejected rather than running a pathological match.
STORED_PATTERN_UNSAFE_ERROR_TEXT = (
    "The proband ID validation pattern configured for this study is not safe to "
    "evaluate (it can cause catastrophic backtracking) and must be fixed by a study "
    "administrator."
)

# Shown to the pattern author (study-config UI / save path) when a pattern is rejected
# for being prone to catastrophic backtracking.
UNSAFE_PATTERN_ERROR_TEXT = (
    "This proband ID validation pattern is rejected because it contains nested "
    "unbounded quantifiers (for example '(a+)+' or '(.*)*'), which can cause "
    "catastrophic backtracking and hang the server. Rewrite it using bounded "
    "quantifiers such as '{1,20}' or a plain character class."
)

# --- Resource-exhaustion bounds (issue #318, item 6) -------------------------------
# The match paths run an admin-authored (interview / saved-study /validate) or, on the
# stateless test endpoint, a caller-authored regex. Python's stdlib ``re`` has no match
# timeout, and empirically a pathological pattern such as ``(a+)+`` blows up at only ~30
# characters of input and — even offloaded to a worker thread — starves the asyncio event
# loop (the GIL is not released usefully during a match). So the mitigation is *structural*
# rather than a timeout: reject dangerous patterns before any match runs, plus hard length
# caps so the input feeding a match is bounded. See ``pattern_safety_error`` below.
MAX_PROBAND_ID_LENGTH = 256  # cap on a single proband ID / sample fed to a match
MAX_PROBAND_ID_PATTERN_LENGTH = 1024  # mirrors Study.proband_external_id_pattern max_length


def _pattern_has_nested_unbounded_repeat(pattern: str) -> bool:
    """Best-effort detector for the dominant catastrophic-backtracking shape: an unbounded
    quantifier (``*``, ``+``, ``{n,}``) nested inside another unbounded quantifier, e.g.
    ``(a+)+``, ``(a*)*``, ``(.*)+``.

    This is a heuristic, NOT a proof — deciding catastrophic backtracking in general is
    undecidable. It deliberately targets only the nested-unbounded-repeat family (by far
    the most common ReDoS class). Alternation-overlap catastrophes such as ``(a|a)+`` are
    *not* detected here; those remain residual risk mitigated by the length caps and, on
    the test endpoint, the study-admin authorization requirement.

    Uses CPython's private ``re`` parser. If those internals ever change shape we fail
    *open* (return ``False``) so a legitimate pattern is never wrongly rejected — the
    length caps and (for saved studies) the compile check remain as the floor.
    """
    try:
        import re._parser as _reparser
        import re._constants as _reconst
    except Exception:  # pragma: no cover - defensive: private module moved/renamed
        return False
    try:
        parsed = _reparser.parse(pattern)
    except Exception:
        # Does not parse/compile -> not this function's concern (the compile check reports
        # it). Treat as "not detected here".
        return False

    unbounded = _reconst.MAXREPEAT

    def walk(seq, inside_unbounded: bool) -> bool:
        for op, av in seq:
            if op in (_reconst.MAX_REPEAT, _reconst.MIN_REPEAT):
                _min, _max, sub = av
                this_unbounded = _max is unbounded
                if this_unbounded and inside_unbounded:
                    return True
                if walk(sub, inside_unbounded or this_unbounded):
                    return True
            elif op is _reconst.SUBPATTERN:
                # av = (group, add_flags, del_flags, sub)
                if walk(av[3], inside_unbounded):
                    return True
            elif op is _reconst.BRANCH:
                # av = (None, [seq, seq, ...])
                for alt in av[1]:
                    if walk(alt, inside_unbounded):
                        return True
            elif op is _reconst.ATOMIC_GROUP:
                if walk(av, inside_unbounded):
                    return True
            elif op in (_reconst.ASSERT, _reconst.ASSERT_NOT):
                # av = (direction, sub)
                if walk(av[1], inside_unbounded):
                    return True
        return False

    try:
        return walk(parsed, False)
    except Exception:  # pragma: no cover - defensive: unexpected parse-tree shape
        return False


def pattern_safety_error(pattern: Optional[str]) -> Optional[str]:
    """Return a human-readable rejection reason if ``pattern`` is unsafe to evaluate, else
    ``None``. Covers the length cap and the nested-unbounded-quantifier check. Empty/``None``
    patterns (accept-anything) are always safe."""
    if pattern in (None, ""):
        return None
    if len(pattern) > MAX_PROBAND_ID_PATTERN_LENGTH:
        return (
            f"Pattern is too long (max {MAX_PROBAND_ID_PATTERN_LENGTH} characters)."
        )
    if _pattern_has_nested_unbounded_repeat(pattern):
        return UNSAFE_PATTERN_ERROR_TEXT
    return None


class ProbandIdCheckResult(MedLogBaseModel):
    """Full structured outcome of a normalize+validate check (internal, superset).

    ``pattern_compiles`` is ``True`` when there is no pattern at all (nothing to break).
    """

    valid: bool
    normalized: str
    error_text: Optional[str] = None
    pattern_compiles: bool = True
    # False when the pattern compiles but is rejected as unsafe to evaluate (item 6).
    pattern_safe: bool = True


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
    pattern_safe: bool = True
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
    # False when the pattern compiles but is rejected as unsafe (nested unbounded
    # quantifiers). Lets the UI show 'rewrite this pattern' distinctly from 'sample did
    # not match'.
    pattern_safe: bool = True


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
    pattern = pattern.strip()
    if pattern in (None, ""):
        # No pattern -> nothing is evaluated, so no ReDoS surface and no length cap needed.
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
    # Item 6 (catastrophic-backtracking guard): reject unsafe patterns *before* running any
    # match. re.fullmatch has no timeout and a pathological pattern blocks the event loop
    # (see the resource-exhaustion note near MAX_PROBAND_ID_LENGTH), so the guard is
    # structural: never run a match against a pattern with nested unbounded quantifiers.
    # Callers that persist patterns already reject these at save time; this is the
    # single-choke-point backstop that also covers pre-existing / directly-written rows.
    if pattern_safety_error(pattern) is not None:
        return ProbandIdCheckResult(
            valid=False,
            normalized=normalized,
            error_text=UNSAFE_PATTERN_ERROR_TEXT,
            pattern_compiles=True,
            pattern_safe=False,
        )
    # Bound the input actually fed to the matcher. Also enforced at the API boundary
    # (max_length on the request models), so this is a backstop for direct/unit callers.
    if len(normalized) > MAX_PROBAND_ID_LENGTH:
        return ProbandIdCheckResult(
            valid=False,
            normalized=normalized,
            error_text=(
                f"Proband ID is too long to validate (max {MAX_PROBAND_ID_LENGTH} "
                "characters)."
            ),
            pattern_compiles=True,
            pattern_safe=True,
        )
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
    if not result.pattern_safe:
        # Stored pattern is structurally unsafe -> fail closed with an admin-facing message
        # (never run the pathological match). Save-time rejection prevents new such rows;
        # this covers migrated / directly-written ones.
        return False, result.normalized, STORED_PATTERN_UNSAFE_ERROR_TEXT
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
    # Item 6: also reject patterns prone to catastrophic backtracking so they can never be
    # stored and then hang interview creation / the /validate endpoint.
    unsafe_reason = pattern_safety_error(pattern)
    if unsafe_reason is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=unsafe_reason,
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
