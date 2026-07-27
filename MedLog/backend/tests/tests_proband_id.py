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
"""

import datetime
import importlib.util
from pathlib import Path

import sqlalchemy as sa

from utils import (
    req,
    create_test_study,
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
            "intake_start_date": datetime.date.today().isoformat(),
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
    assert body["detail"] == ERROR_TEXT, body


def test_invalid_id_rejected_generic_fallback_when_no_error_text():
    study_id, event_id = _setup_study("probandid_invalid_generic", pattern=PATTERN)
    body = _create_interview(study_id, event_id, "xxx", expected_http_code=422)
    # generic fallback text (not None, not empty)
    assert isinstance(body["detail"], str) and body["detail"], body
    assert "format" in body["detail"].lower(), body


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


def test_fullmatch_rejects_trailing_newline():
    # Classic `$`-vs-`\Z` trap: "$" can match before a trailing newline, but
    # re.fullmatch must reject the newline because it is not consumed.
    study_id, _ = _setup_study("probandid_fullmatch_newline", pattern=PATTERN)
    assert _validate(study_id, "AAA1111\n")["valid"] is False


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
