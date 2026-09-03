"""Adversarial tests for the per-study proband-external-ID validation + normalization
feature (branch feature/probandid-check, issue #318).

Covers:
- no pattern => accept anything
- pattern configured => valid accepted / invalid rejected (422 + error text)
- normalization (uppercase/lowercase/none): storage + case significance
- matching across normalization on the interview / last-interview / intake read endpoints
- invalid regex on study create/update => 422
- POST .../proband-external-id/validate endpoint
- re.fullmatch anchoring (partial matches rejected)
- fail-closed check_proband_id on an uncompilable stored pattern (unit)
- migration e5f6a7b8c9d0 upgrade/backfill (lightweight sqlite alembic check)
- item 6 (ReDoS hardening): catastrophic-backtracking pattern rejection at save time,
  at match time (fail-closed), and on the stateless test endpoint; input/pattern length
  caps; and least-privilege authorization on the stateless test endpoint
"""

import datetime
import importlib.util
import time
from pathlib import Path

import sqlalchemy as sa

from utils import (
    req,
    create_test_study,
    create_test_user,
    authorize_for_access_token,
    dictyfy,
    utc_today_iso,
)

BACKEND_DIR = Path(__file__).resolve().parent.parent

PATTERN = "^[A-Z]{3}[0-9]{4}$"
ERROR_TEXT = "Expected 3 uppercase letters followed by 4 digits, e.g. AAA1111"


# ─────────────────────────── helpers ────────────────────────────────────────


def _setup_study(
    name: str,
    pattern: str = None,
    error_text: str = None,
    normalization: str = None,
    with_events: int = 1,
):
    """Create a study (via the shared helper) then PATCH the proband-ID rules onto it.
    Returns (study_id, first_event_id_or_None)."""
    data = create_test_study(study_name=name, with_events=with_events)
    patch_body = {}
    if pattern is not None:
        patch_body["proband_external_id_pattern"] = pattern
    if error_text is not None:
        patch_body["proband_external_id_pattern_error_text"] = error_text
    if normalization is not None:
        patch_body["proband_external_id_normalization"] = normalization
    if patch_body:
        updated = req(f"api/study/{data.study.id}", method="patch", b=patch_body)
        # sanity: the rules round-tripped
        if normalization is not None:
            assert updated["proband_external_id_normalization"] == normalization, updated
        if pattern is not None:
            assert updated["proband_external_id_pattern"] == pattern, updated
    event_id = data.events[0].event.id if with_events else None
    return str(data.study.id), (str(event_id) if event_id else None)


def _create_interview(study_id, event_id, proband_external_id, expected_http_code=None,
                      completed=False):
    body = {
        "proband_external_id": proband_external_id,
        "interview_start_time_utc": datetime.datetime.now().isoformat(),
        "proband_has_taken_meds": True,
    }
    if completed:
        body["interview_end_time_utc"] = datetime.datetime.now().isoformat()
    return req(
        f"api/study/{study_id}/event/{event_id}/interview",
        method="post",
        b=body,
        expected_http_code=expected_http_code,
    )


def _create_intake(study_id, interview_id):
    """Create a single intake in an interview (mirrors tests/utils.create_test_study)."""
    drug_search_result = req("/api/drug/search", method="get", q={"search_term": "Test2Drug"})
    drug_id = drug_search_result["items"][0]["drug"]["id"]
    return req(
        f"api/study/{study_id}/interview/{interview_id}/intake",
        method="post",
        b={
            "drug_id": drug_id,
            "intake_start_date": utc_today_iso(),
            "intake_end_date": None,
            "consumed_meds_today": "No",
            "as_needed_dose_unit": None,
        },
    )


def _validate(study_id, proband_external_id):
    return req(
        f"api/study/{study_id}/proband-external-id/validate",
        method="post",
        b={"proband_external_id": proband_external_id},
    )


# ─────────────────────── no pattern => accept anything ───────────────────────


def test_no_pattern_accepts_anything():
    study_id, event_id = _setup_study("probandid_no_pattern")
    # weird ID with symbols must still be accepted (status quo default)
    weird = "any-thing_!@#123"
    interview = _create_interview(study_id, event_id, weird)
    assert interview["proband_external_id"] == weird
    # validate endpoint agrees
    res = _validate(study_id, weird)
    assert res["valid"] is True
    assert res["error_text"] is None
    assert res["normalized_proband_external_id"] == weird


def test_empty_pattern_accepts_anything():
    # A pattern of "" must behave exactly like None (accept anything).
    study_id, event_id = _setup_study("probandid_empty_pattern", pattern="")
    res = _validate(study_id, "literally anything")
    assert res["valid"] is True, res


# ─────────────────── pattern configured: valid / invalid ─────────────────────


def test_valid_id_accepted():
    study_id, event_id = _setup_study(
        "probandid_valid_ok", pattern=PATTERN, error_text=ERROR_TEXT
    )
    interview = _create_interview(study_id, event_id, "ABC1234")
    assert interview["proband_external_id"] == "ABC1234"


def test_invalid_id_rejected_with_configured_error_text():
    study_id, event_id = _setup_study(
        "probandid_invalid_422", pattern=PATTERN, error_text=ERROR_TEXT
    )
    body = _create_interview(study_id, event_id, "not-matching", expected_http_code=422)
    # item 3: detail is now a structured object {message, normalized_proband_external_id}
    assert body["detail"]["message"] == ERROR_TEXT, body
    assert body["detail"]["normalized_proband_external_id"] == "not-matching", body


def test_invalid_id_rejected_generic_fallback_when_no_error_text():
    study_id, event_id = _setup_study("probandid_invalid_generic", pattern=PATTERN)
    body = _create_interview(study_id, event_id, "xxx", expected_http_code=422)
    # generic fallback text (not None, not empty)
    msg = body["detail"]["message"]
    assert isinstance(msg, str) and msg, body
    assert "format" in msg.lower(), body


# ─────────────────────────── normalization ──────────────────────────────────


def test_uppercase_normalization_stores_uppercased():
    study_id, event_id = _setup_study(
        "probandid_upper_store", pattern=PATTERN, normalization="uppercase"
    )
    # lowercase input folds to AAA1111 -> matches uppercase pattern
    interview = _create_interview(study_id, event_id, "aaa1111")
    assert interview["proband_external_id"] == "AAA1111", interview
    # confirm what is actually stored via the list endpoint
    listed = req(f"api/study/{study_id}/event/{event_id}/interview", method="get")
    assert len(listed) == 1
    assert listed[0]["proband_external_id"] == "AAA1111", listed


def test_lowercase_normalization_stores_lowercased():
    study_id, event_id = _setup_study(
        "probandid_lower_store", pattern="^[a-z]{3}[0-9]{4}$", normalization="lowercase"
    )
    interview = _create_interview(study_id, event_id, "AAA1111")
    assert interview["proband_external_id"] == "aaa1111", interview


def test_none_normalization_case_significant():
    # With normalization=none, a lowercase input does NOT match an uppercase pattern.
    study_id, event_id = _setup_study(
        "probandid_none_case", pattern=PATTERN, normalization="none"
    )
    _create_interview(study_id, event_id, "aaa1111", expected_http_code=422)
    # exact-case input is accepted and stored verbatim
    interview = _create_interview(study_id, event_id, "AAA1111")
    assert interview["proband_external_id"] == "AAA1111", interview


def test_uppercase_dedup_collapses_case():
    # The one-interview-per-event guard must treat aaa1111 and AAA1111 as the same
    # proband under uppercase normalization (409 on the second).
    study_id, event_id = _setup_study(
        "probandid_upper_dedup", pattern=PATTERN, normalization="uppercase"
    )
    _create_interview(study_id, event_id, "aaa1111")
    _create_interview(study_id, event_id, "AAA1111", expected_http_code=409)


# ─────────────── matching across normalization (read endpoints) ──────────────


def test_matching_across_normalization_uppercase_interview_endpoints():
    """Interview stored uppercased is found by a lookup in a different case."""
    study_id, event_id = _setup_study(
        "probandid_match_upper", pattern=PATTERN, normalization="uppercase"
    )
    # stored as AAA1111 (completed so 'last' endpoint returns it)
    _create_interview(study_id, event_id, "aaa1111", completed=True)

    for lookup in ("AAA1111", "aaa1111", "AaA1111"):
        listed = req(
            f"api/study/{study_id}/proband/{lookup}/interview", method="get"
        )
        assert len(listed) == 1, (lookup, listed)

        last = req(
            f"api/study/{study_id}/proband/{lookup}/interview/last",
            method="get",
            tolerated_error_codes=[204],
        )
        assert isinstance(last, dict) and last.get("proband_external_id") == "AAA1111", (
            lookup,
            last,
        )


def test_matching_none_is_case_sensitive_interview_endpoints():
    """Under normalization=none, stored data is matched exactly (legacy-safe)."""
    study_id, event_id = _setup_study(
        "probandid_match_none", normalization="none"
    )  # no pattern => any id accepted, stored verbatim
    _create_interview(study_id, event_id, "AAA1111", completed=True)

    # exact case: found
    listed_exact = req(
        f"api/study/{study_id}/proband/AAA1111/interview", method="get"
    )
    assert len(listed_exact) == 1, listed_exact

    # different case: NOT found (no data rewrite / no case folding)
    listed_other = req(
        f"api/study/{study_id}/proband/aaa1111/interview", method="get"
    )
    assert len(listed_other) == 0, listed_other

    last_other = req(
        f"api/study/{study_id}/proband/aaa1111/interview/last",
        method="get",
        tolerated_error_codes=[204],
    )
    # 204 => req returns the (empty) body; must not be a matching interview dict
    assert not (isinstance(last_other, dict) and last_other.get("proband_external_id")), (
        last_other
    )


def test_matching_across_normalization_intake_endpoint_uppercase():
    study_id, event_id = _setup_study(
        "probandid_match_intake_upper", pattern=PATTERN, normalization="uppercase"
    )
    interview = _create_interview(study_id, event_id, "aaa1111", completed=True)
    _create_intake(study_id, interview["id"])

    for lookup in ("AAA1111", "aaa1111"):
        intakes = req(f"api/study/{study_id}/proband/{lookup}/intake", method="get")
        assert intakes["count"] == 1, (lookup, intakes)


def test_matching_intake_none_is_case_sensitive():
    study_id, event_id = _setup_study(
        "probandid_match_intake_none", normalization="none"
    )
    interview = _create_interview(study_id, event_id, "AAA1111", completed=True)
    _create_intake(study_id, interview["id"])

    found = req(f"api/study/{study_id}/proband/AAA1111/intake", method="get")
    assert found["count"] == 1, found

    not_found = req(f"api/study/{study_id}/proband/aaa1111/intake", method="get")
    assert not_found["count"] == 0, not_found


# ─────────────────────── invalid regex on create/update ──────────────────────


def test_invalid_regex_on_create_rejected():
    from medlogserver.model.study import StudyCreateAPI
    from utils import dictyfy

    body = dictyfy(
        StudyCreateAPI(
            display_name="probandid_bad_regex_create",
            proband_external_id_pattern="[unclosed",
        )
    )
    req("api/study", method="post", b=body, expected_http_code=422)


def test_invalid_regex_on_update_rejected():
    study_id, _ = _setup_study("probandid_bad_regex_update")
    req(
        f"api/study/{study_id}",
        method="patch",
        b={"proband_external_id_pattern": "(unbalanced"},
        expected_http_code=422,
    )


# ─────────────────────────── /validate endpoint ──────────────────────────────


def test_validate_bad_id_returns_false_without_creating():
    study_id, event_id = _setup_study(
        "probandid_validate_bad", pattern=PATTERN, error_text=ERROR_TEXT
    )
    res = _validate(study_id, "bad")
    assert res["valid"] is False, res
    assert res["error_text"] == ERROR_TEXT, res
    assert res["normalized_proband_external_id"] == "bad", res
    # nothing was created
    listed = req(f"api/study/{study_id}/event/{event_id}/interview", method="get")
    assert len(listed) == 0, listed


def test_validate_good_id_returns_true():
    study_id, _ = _setup_study(
        "probandid_validate_good", pattern=PATTERN, error_text=ERROR_TEXT
    )
    res = _validate(study_id, "ABC1234")
    assert res["valid"] is True, res
    assert res["error_text"] is None, res
    assert res["normalized_proband_external_id"] == "ABC1234", res


def test_validate_normalizes_before_validating():
    study_id, _ = _setup_study(
        "probandid_validate_norm", pattern=PATTERN, normalization="uppercase"
    )
    res = _validate(study_id, "aaa1111")
    assert res["valid"] is True, res
    assert res["normalized_proband_external_id"] == "AAA1111", res


# ─────────────────────── re.fullmatch anchoring ──────────────────────────────


def test_fullmatch_rejects_partial_matches():
    study_id, _ = _setup_study("probandid_fullmatch", pattern=PATTERN)
    assert _validate(study_id, "AAA1111")["valid"] is True
    # trailing extra char
    assert _validate(study_id, "AAA1111X")["valid"] is False
    # leading extra char
    assert _validate(study_id, "XAAA1111")["valid"] is False
    # embedded
    assert _validate(study_id, "AAA11119")["valid"] is False


def test_fullmatch_anchors_even_without_explicit_anchors():
    # Pattern WITHOUT ^...$ — re.fullmatch must still require a full-string match.
    study_id, _ = _setup_study("probandid_fullmatch_noanchor", pattern="[A-Z]{3}[0-9]{4}")
    assert _validate(study_id, "ABC1234")["valid"] is True
    assert _validate(study_id, "ABC1234X")["valid"] is False
    assert _validate(study_id, "XABC1234")["valid"] is False


def test_trailing_newline_is_trimmed_then_accepted():
    # Since item 1, leading/trailing whitespace (incl. "\n") is trimmed BEFORE validation,
    # so "AAA1111\n" normalizes to "AAA1111" and is accepted. This supersedes the former
    # "$-vs-\\Z trailing-newline is rejected" expectation: the newline never reaches the
    # matcher. Internal newlines are still rejected (see below).
    study_id, _ = _setup_study("probandid_fullmatch_newline", pattern=PATTERN)
    res = _validate(study_id, "AAA1111\n")
    assert res["valid"] is True, res
    assert res["normalized_proband_external_id"] == "AAA1111", res


def test_fullmatch_rejects_internal_newline():
    # Anchoring trap that trimming cannot rescue: a newline in the MIDDLE of the value.
    # "$" in multiline-less mode still would not help; re.fullmatch requires the whole
    # (trimmed) string to match, so an embedded newline is rejected.
    study_id, _ = _setup_study("probandid_fullmatch_internal_nl", pattern=PATTERN)
    assert _validate(study_id, "AAA\n1111")["valid"] is False


# ─────────────── fail-closed on uncompilable stored pattern (unit) ───────────


def test_check_proband_id_fails_closed_on_bad_stored_pattern():
    from medlogserver.api.proband_id import check_proband_id
    from medlogserver.model.study import Study, ProbandExternalIdNormalization

    study = Study(
        display_name="broken_pattern_study",
        proband_external_id_pattern="[unclosed",  # cannot compile
        proband_external_id_normalization=ProbandExternalIdNormalization.NONE,
    )
    valid, normalized, error_text = check_proband_id(study, "AAA1111")
    assert valid is False, (valid, error_text)
    assert normalized == "AAA1111"
    assert error_text and "administrator" in error_text.lower(), error_text


# ─────────────────────────── item 1: whitespace trimming ────────────────────


def _validate_pattern(pattern, sample, normalization=None):
    body = {"sample": sample}
    if pattern is not None:
        body["pattern"] = pattern
    if normalization is not None:
        body["normalization"] = normalization
    return req(
        "api/proband-external-id/validate-pattern", method="post", b=body
    )


def test_trailing_whitespace_trimmed_with_pattern():
    # "AAA1111 " (trailing space) must be accepted and stored WITHOUT the space,
    # even though the pattern itself has no allowance for whitespace.
    study_id, event_id = _setup_study(
        "probandid_trim_pattern", pattern=PATTERN, normalization="none"
    )
    interview = _create_interview(study_id, event_id, "AAA1111 ")
    assert interview["proband_external_id"] == "AAA1111", interview
    # leading space too
    interview2 = _create_interview(study_id, event_id, "  BBB2222", completed=True)
    assert interview2["proband_external_id"] == "BBB2222", interview2


def test_whitespace_variants_resolve_to_same_value_without_pattern():
    # With no pattern and normalization=none, "AAA1111 " and "AAA1111" must resolve to the
    # same stored/lookup value (else a space would silently break later lookups).
    study_id, event_id = _setup_study("probandid_trim_nopattern", normalization="none")
    interview = _create_interview(study_id, event_id, "AAA1111 ", completed=True)
    assert interview["proband_external_id"] == "AAA1111", interview

    # lookup by the un-spaced value finds it
    listed = req(f"api/study/{study_id}/proband/AAA1111/interview", method="get")
    assert len(listed) == 1, listed
    # lookup by the spaced value also finds it (input is trimmed before matching)
    listed_spaced = req(
        f"api/study/{study_id}/proband/AAA1111%20/interview", method="get"
    )
    assert len(listed_spaced) == 1, listed_spaced

    # a second interview with the spaced value collapses onto the same proband (409 guard)
    _create_interview(study_id, event_id, "AAA1111 ", expected_http_code=409)


def test_validate_endpoint_trims_whitespace():
    study_id, _ = _setup_study("probandid_trim_validate", pattern=PATTERN)
    res = _validate(study_id, " AAA1111 ")
    assert res["valid"] is True, res
    assert res["normalized_proband_external_id"] == "AAA1111", res


# ─────────────────── item 2: stateless validate-pattern endpoint ─────────────


def test_validate_pattern_bad_regex_reports_pattern_compiles_false():
    res = _validate_pattern("[unclosed", "AAA1111")
    assert res["pattern_compiles"] is False, res
    assert res["valid"] is False, res
    assert res["error_text"], res


def test_validate_pattern_partial_match_rejected_fullmatch():
    # fullmatch semantics: a partial match must be rejected even though re.match would pass.
    res_ok = _validate_pattern(PATTERN, "AAA1111")
    assert res_ok["valid"] is True and res_ok["pattern_compiles"] is True, res_ok
    res_bad = _validate_pattern(PATTERN, "AAA1111X")
    assert res_bad["valid"] is False and res_bad["pattern_compiles"] is True, res_bad


def test_validate_pattern_applies_normalization_to_sample():
    res = _validate_pattern(PATTERN, "aaa1111", normalization="uppercase")
    assert res["valid"] is True, res
    assert res["normalized_sample"] == "AAA1111", res


def test_validate_pattern_no_pattern_accepts_anything():
    res = _validate_pattern(None, "literally anything")
    assert res["valid"] is True, res
    assert res["pattern_compiles"] is True, res


def test_validate_pattern_trims_sample():
    res = _validate_pattern(PATTERN, "  AAA1111  ")
    assert res["valid"] is True, res
    assert res["normalized_sample"] == "AAA1111", res


def test_validate_pattern_requires_auth():
    # No bearer token -> 401/403 (endpoint requires an authenticated user).
    req(
        "api/proband-external-id/validate-pattern",
        method="post",
        b={"pattern": PATTERN, "sample": "AAA1111"},
        suppress_auth=True,
        tolerated_error_codes=[401, 403],
    )


# ─────────────── item 3: structured error surfaces normalized value ──────────


def test_interview_422_surfaces_normalized_value():
    # aaa1111 is uppercased to AAA1111 which still does not match a digits-only pattern.
    study_id, event_id = _setup_study(
        "probandid_norm_surface", pattern="^[0-9]{7}$", normalization="uppercase"
    )
    body = _create_interview(study_id, event_id, "aaa1111", expected_http_code=422)
    assert body["detail"]["normalized_proband_external_id"] == "AAA1111", body
    assert body["detail"]["message"], body


def test_validate_endpoint_surfaces_normalized_value_on_reject():
    study_id, _ = _setup_study(
        "probandid_norm_surface_validate",
        pattern="^[0-9]{7}$",
        normalization="uppercase",
    )
    res = _validate(study_id, "aaa1111")
    assert res["valid"] is False, res
    assert res["normalized_proband_external_id"] == "AAA1111", res


def test_validate_pattern_surfaces_normalized_sample_on_reject():
    res = _validate_pattern("^[0-9]{7}$", "aaa1111", normalization="uppercase")
    assert res["valid"] is False, res
    assert res["normalized_sample"] == "AAA1111", res


# ─────────────────────── item 4: positive example field ──────────────────────


def test_example_round_trips_on_create_and_update():
    from medlogserver.model.study import StudyCreateAPI
    from utils import dictyfy

    body = dictyfy(
        StudyCreateAPI(
            display_name="probandid_example_create",
            proband_external_id_example="AAA1111",
        )
    )
    created = req("api/study", method="post", b=body)
    assert created["proband_external_id_example"] == "AAA1111", created

    # present in study GET (list)
    listed = req("api/study", method="get")
    from utils import find_first_dict_in_list

    study_in_list = find_first_dict_in_list(
        listed["items"], required_keys_and_val={"id": created["id"]}
    )
    assert study_in_list["proband_external_id_example"] == "AAA1111", study_in_list

    # update it
    updated = req(
        f"api/study/{created['id']}",
        method="patch",
        b={"proband_external_id_example": "BBB2222"},
    )
    assert updated["proband_external_id_example"] == "BBB2222", updated


def test_example_included_in_validate_response():
    study_id, _ = _setup_study("probandid_example_validate", pattern=PATTERN)
    req(
        f"api/study/{study_id}",
        method="patch",
        b={"proband_external_id_example": "AAA1111"},
    )
    res = _validate(study_id, "ABC1234")
    assert res["proband_external_id_example"] == "AAA1111", res


# ─────────── item 5: guard normalization change on a populated study ─────────


def test_normalization_change_blocked_on_populated_study():
    study_id, event_id = _setup_study(
        "probandid_normguard_blocked", normalization="none"
    )
    _create_interview(study_id, event_id, "AAA1111")
    # attempt to switch normalization -> 409 without confirmation
    body = req(
        f"api/study/{study_id}",
        method="patch",
        b={"proband_external_id_normalization": "uppercase"},
        expected_http_code=409,
    )
    assert body["detail"]["affected_interview_count"] == 1, body


def test_normalization_change_allowed_with_confirmation():
    study_id, event_id = _setup_study(
        "probandid_normguard_confirmed", normalization="none"
    )
    _create_interview(study_id, event_id, "AAA1111")
    updated = req(
        f"api/study/{study_id}?confirm_normalization_change=true",
        method="patch",
        b={"proband_external_id_normalization": "uppercase"},
    )
    assert updated["proband_external_id_normalization"] == "uppercase", updated


def test_normalization_change_allowed_when_no_interviews():
    study_id, _ = _setup_study("probandid_normguard_empty", normalization="none")
    # no interviews -> change goes through without confirmation
    updated = req(
        f"api/study/{study_id}",
        method="patch",
        b={"proband_external_id_normalization": "uppercase"},
    )
    assert updated["proband_external_id_normalization"] == "uppercase", updated


def test_same_normalization_update_not_blocked_on_populated_study():
    # PATCHing other fields (or the same normalization value) must NOT trip the guard.
    study_id, event_id = _setup_study(
        "probandid_normguard_noop", normalization="uppercase"
    )
    _create_interview(study_id, event_id, "AAA1111")
    updated = req(
        f"api/study/{study_id}",
        method="patch",
        b={
            "proband_external_id_normalization": "uppercase",
            "proband_external_id_example": "AAA1111",
        },
    )
    assert updated["proband_external_id_example"] == "AAA1111", updated


# ─────────────────────────── migration e5f6a7b8c9d0 ─────────────────────────


def _load_migration_module():
    mig_path = (
        BACKEND_DIR
        / "medlogserver/db_migrations/versions/"
        "e5f6a7b8c9d0_add_proband_external_id_validation_to_study.py"
    )
    spec = importlib.util.spec_from_file_location("mig_e5f6a7b8c9d0", mig_path)
    mig = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mig)
    return mig


def _run_migration_func(mig, func_name, connection):
    from alembic.runtime.migration import MigrationContext
    from alembic.operations import Operations

    ctx = MigrationContext.configure(connection)
    ops = Operations(ctx)
    old_op = mig.op
    mig.op = ops
    try:
        getattr(mig, func_name)()
    finally:
        mig.op = old_op


def _prepare_study_table(engine):
    with engine.begin() as conn:
        conn.execute(
            sa.text("CREATE TABLE study (id VARCHAR PRIMARY KEY, display_name VARCHAR)")
        )
        conn.execute(
            sa.text("INSERT INTO study (id, display_name) VALUES ('s1', 'Existing')")
        )


def test_migration_upgrade_backfills_lowercase_when_case_insensitive(tmp_path, monkeypatch):
    monkeypatch.delenv("PROBAND_IDS_CASE_SENSETIVE", raising=False)  # default => case-insensitive
    mig = _load_migration_module()
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'mig_ci.db'}")
    _prepare_study_table(engine)
    with engine.begin() as conn:
        _run_migration_func(mig, "upgrade", conn)

    with engine.connect() as conn:
        cols = [r[1] for r in conn.execute(sa.text("PRAGMA table_info(study)"))]
        assert "proband_external_id_pattern" in cols
        assert "proband_external_id_pattern_error_text" in cols
        assert "proband_external_id_normalization" in cols
        val = conn.execute(
            sa.text("SELECT proband_external_id_normalization FROM study WHERE id='s1'")
        ).scalar()
        assert val == "LOWERCASE", val


def test_migration_upgrade_backfills_none_when_case_sensitive(tmp_path, monkeypatch):
    monkeypatch.setenv("PROBAND_IDS_CASE_SENSETIVE", "true")
    mig = _load_migration_module()
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'mig_cs.db'}")
    _prepare_study_table(engine)
    with engine.begin() as conn:
        _run_migration_func(mig, "upgrade", conn)

    with engine.connect() as conn:
        val = conn.execute(
            sa.text("SELECT proband_external_id_normalization FROM study WHERE id='s1'")
        ).scalar()
        assert val == "NONE", val


def test_migration_downgrade_removes_columns(tmp_path, monkeypatch):
    monkeypatch.delenv("PROBAND_IDS_CASE_SENSETIVE", raising=False)
    mig = _load_migration_module()
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'mig_down.db'}")
    _prepare_study_table(engine)
    with engine.begin() as conn:
        _run_migration_func(mig, "upgrade", conn)
    with engine.begin() as conn:
        _run_migration_func(mig, "downgrade", conn)

    with engine.connect() as conn:
        cols = [r[1] for r in conn.execute(sa.text("PRAGMA table_info(study)"))]
        assert "proband_external_id_pattern" not in cols
        assert "proband_external_id_normalization" not in cols


# ─────────────────────────── migration f6a7b8c9d0e1 (item 4) ─────────────────


def _load_example_migration_module():
    mig_path = (
        BACKEND_DIR
        / "medlogserver/db_migrations/versions/"
        "f6a7b8c9d0e1_add_proband_external_id_example_to_study.py"
    )
    spec = importlib.util.spec_from_file_location("mig_f6a7b8c9d0e1", mig_path)
    mig = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mig)
    return mig


def test_example_migration_upgrade_and_downgrade(tmp_path):
    mig = _load_example_migration_module()
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'mig_example.db'}")
    _prepare_study_table(engine)

    with engine.begin() as conn:
        _run_migration_func(mig, "upgrade", conn)
    with engine.connect() as conn:
        cols = [r[1] for r in conn.execute(sa.text("PRAGMA table_info(study)"))]
        assert "proband_external_id_example" in cols

    with engine.begin() as conn:
        _run_migration_func(mig, "downgrade", conn)
    with engine.connect() as conn:
        cols = [r[1] for r in conn.execute(sa.text("PRAGMA table_info(study)"))]
        assert "proband_external_id_example" not in cols


# ══════════════════ item 6: ReDoS / resource-exhaustion hardening ═════════════
#
# A pattern such as (a+)+ backtracks catastrophically: empirically it blows up at ~30
# characters of input and — because Python's re has no timeout and does not usefully
# release the GIL during a match — a single request can starve the whole async event
# loop. The mitigation is structural: never *run* a match against such a pattern. It is
# rejected (a) at save time, (b) at match time as a fail-closed backstop, and (c) on the
# stateless test endpoint. Length caps bound the input feeding any match, and the test
# endpoint is additionally restricted to study administrators.

# A textbook catastrophic-backtracking pattern (nested unbounded quantifiers).
CATASTROPHIC_PATTERN = "(a+)+$"
# An input that would take many seconds against CATASTROPHIC_PATTERN if it ever ran.
REDOS_ATTACK_INPUT = "a" * 40 + "!"


# ── save-time rejection ──────────────────────────────────────────────────────


def test_catastrophic_pattern_rejected_on_create():
    from medlogserver.model.study import StudyCreateAPI

    body = dictyfy(
        StudyCreateAPI(
            display_name="probandid_redos_create",
            proband_external_id_pattern=CATASTROPHIC_PATTERN,
        )
    )
    res = req("api/study", method="post", b=body, expected_http_code=422)
    # the rejection must explain *why* (not a generic compile error)
    detail = res["detail"]
    detail_text = detail if isinstance(detail, str) else str(detail)
    assert "backtrack" in detail_text.lower(), res


def test_catastrophic_pattern_rejected_on_update():
    study_id, _ = _setup_study("probandid_redos_update")
    req(
        f"api/study/{study_id}",
        method="patch",
        b={"proband_external_id_pattern": "(.*)*x"},
        expected_http_code=422,
    )


def test_various_catastrophic_shapes_rejected_but_safe_patterns_allowed():
    from medlogserver.model.study import StudyCreateAPI

    # These must all be rejected at save time.
    for i, pat in enumerate(["(a*)*", "(a+)+", "([a-z]+)*@", "(.*)+", "((ab)+)+"]):
        body = dictyfy(
            StudyCreateAPI(
                display_name=f"probandid_redos_bad_{i}",
                proband_external_id_pattern=pat,
            )
        )
        req("api/study", method="post", b=body, expected_http_code=422)

    # These realistic proband-ID patterns must NOT be falsely rejected.
    for i, pat in enumerate(
        ["^[A-Z]{3}[0-9]{4}$", "[A-Za-z0-9_-]{1,20}", r"\d{4}-\d{2}", "[A-Z]+[0-9]+"]
    ):
        body = dictyfy(
            StudyCreateAPI(
                display_name=f"probandid_redos_good_{i}",
                proband_external_id_pattern=pat,
            )
        )
        created = req("api/study", method="post", b=body)
        assert created["proband_external_id_pattern"] == pat, created


# ── stateless test endpoint: rejection is fast (does not hang) ────────────────


def test_validate_pattern_rejects_catastrophic_without_hanging():
    start = time.monotonic()
    res = _validate_pattern(CATASTROPHIC_PATTERN, REDOS_ATTACK_INPUT)
    elapsed = time.monotonic() - start
    # The dangerous match must never run -> the response is effectively instant. If the
    # guard regressed and the match ran, this would take many seconds (or hang).
    assert elapsed < 2.0, f"validate-pattern took {elapsed:.2f}s (guard regressed?)"
    assert res["pattern_compiles"] is True, res  # it DOES compile...
    assert res["pattern_safe"] is False, res  # ...but is rejected as unsafe
    assert res["valid"] is False, res
    assert res["error_text"], res


def test_validate_pattern_safe_pattern_reports_pattern_safe_true():
    res = _validate_pattern(PATTERN, "AAA1111")
    assert res["pattern_safe"] is True, res
    assert res["valid"] is True, res


# ── match-time fail-closed backstop for a stored unsafe pattern (unit) ────────


def test_check_proband_id_fails_closed_on_unsafe_stored_pattern():
    # Mirrors the uncompilable-pattern fail-closed test: a stored pattern that compiles
    # but is unsafe must reject the ID with an admin-facing message and never run the
    # pathological match. (Save-time rejection prevents new such rows; this backstops
    # migrated / directly-written ones.)
    from medlogserver.api.proband_id import check_proband_id
    from medlogserver.model.study import Study, ProbandExternalIdNormalization

    study = Study(
        display_name="unsafe_pattern_study",
        proband_external_id_pattern=CATASTROPHIC_PATTERN,
        proband_external_id_normalization=ProbandExternalIdNormalization.NONE,
    )
    start = time.monotonic()
    valid, normalized, error_text = check_proband_id(study, REDOS_ATTACK_INPUT)
    elapsed = time.monotonic() - start
    assert elapsed < 2.0, f"check_proband_id took {elapsed:.2f}s (match ran?)"
    assert valid is False, (valid, error_text)
    assert error_text and "administrator" in error_text.lower(), error_text


# ── input / pattern length caps ──────────────────────────────────────────────


def test_interview_proband_id_length_cap_enforced():
    # No pattern, but an absurdly long proband ID is still rejected at the API boundary
    # (bounds the input that could feed a matcher on any study).
    study_id, event_id = _setup_study("probandid_len_cap_interview")
    _create_interview(study_id, event_id, "a" * 300, expected_http_code=422)


def test_validate_endpoint_length_cap_enforced():
    study_id, _ = _setup_study("probandid_len_cap_validate", pattern=PATTERN)
    req(
        f"api/study/{study_id}/proband-external-id/validate",
        method="post",
        b={"proband_external_id": "a" * 300},
        expected_http_code=422,
    )


def test_validate_pattern_length_caps_enforced():
    # oversized sample -> 422
    req(
        "api/proband-external-id/validate-pattern",
        method="post",
        b={"pattern": PATTERN, "sample": "a" * 300},
        expected_http_code=422,
    )
    # oversized pattern -> 422
    req(
        "api/proband-external-id/validate-pattern",
        method="post",
        b={"pattern": "a" * 2000, "sample": "AAA1111"},
        expected_http_code=422,
    )


# ── least-privilege authorization on the stateless test endpoint ─────────────


def test_validate_pattern_forbidden_for_non_study_admin():
    # A freshly created user with no study-admin rights (and not an instance admin) must
    # be rejected: the endpoint runs a caller-supplied regex and is admin-only.
    pw = "redos-authz-pw-1"
    user = create_test_user(
        user_name="probandid_redos_plain",
        password=pw,
        email="probandid_redos_plain@test.com",
    )
    token = authorize_for_access_token(
        username=user.user_name, pw=pw, set_as_global_default_login=False
    )
    req(
        "api/proband-external-id/validate-pattern",
        method="post",
        b={"pattern": PATTERN, "sample": "AAA1111"},
        access_token=token,
        tolerated_error_codes=[403],
    )


def test_validate_pattern_forbidden_for_study_viewer_but_allowed_for_study_admin():
    from medlogserver.model.study_permission import StudyPermissonUpdate

    study_id, _ = _setup_study("probandid_redos_authz_study")

    pw = "redos-authz-pw-2"
    user = create_test_user(
        user_name="probandid_redos_viewer",
        password=pw,
        email="probandid_redos_viewer@test.com",
    )
    token = authorize_for_access_token(
        username=user.user_name, pw=pw, set_as_global_default_login=False
    )

    # viewer-only permission -> still forbidden
    req(
        f"/api/study/{study_id}/permissions/{user.id}",
        method="put",
        b=dictyfy(StudyPermissonUpdate(is_study_viewer=1)),
    )
    req(
        "api/proband-external-id/validate-pattern",
        method="post",
        b={"pattern": PATTERN, "sample": "AAA1111"},
        access_token=token,
        tolerated_error_codes=[403],
    )

    # promote to study admin -> now allowed
    req(
        f"/api/study/{study_id}/permissions/{user.id}",
        method="put",
        b=dictyfy(StudyPermissonUpdate(is_study_admin=1)),
    )
    res = req(
        "api/proband-external-id/validate-pattern",
        method="post",
        b={"pattern": PATTERN, "sample": "AAA1111"},
        access_token=token,
    )
    assert res["valid"] is True, res
