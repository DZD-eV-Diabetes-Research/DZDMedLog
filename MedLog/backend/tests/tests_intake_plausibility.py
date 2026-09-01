"""Tests for the intake plausibility rules.

See https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues/338

Two layers are covered:

* the rules themselves and the PATCH field gating, as plain unit tests against
  `medlogserver.model.intake_rules`
* the API behaviour, asserting 422 on POST and PATCH (including the partial
  payload that only sends one of two conflicting fields) and 200 for the
  combinations that are explicitly allowed
"""

import datetime
from types import SimpleNamespace
from typing import Any, Dict

from utils import (
    req,
    create_test_study,
    TestDataContainerStudy,
)


# ── date helpers ───────────────────────────────────────────────────────────
#
# The rules compare against the server's *UTC* date, so every offset here is
# built from the UTC date too. The test machine's local date can be a day off
# that, which would make the exact "tomorrow is a future date" assertion flaky.

_FAR_FUTURE_DAYS = 10
_FAR_PAST_DAYS = 30
# A typo like "0202" instead of "2020", the case the floor is meant to catch.
_TYPO_DATE = datetime.date(202, 1, 1)


def _today() -> datetime.date:
    return datetime.datetime.now(datetime.timezone.utc).date()


def _day_offset(days: int) -> str:
    return (_today() + datetime.timedelta(days=days)).isoformat()


def _future() -> str:
    return _day_offset(_FAR_FUTURE_DAYS)


def _tomorrow() -> str:
    return _day_offset(1)


def _past() -> str:
    return _day_offset(-_FAR_PAST_DAYS)


# ── test context ───────────────────────────────────────────────────────────

_CONTEXT: Dict[str, Any] = {}


def _context() -> Dict[str, Any]:
    """One study/interview/drug for the whole module, created on first use."""
    if not _CONTEXT:
        study_data: TestDataContainerStudy = create_test_study(
            study_name="TestIntakePlausibilityStudy",
            with_events=1,
            with_interviews_per_event_per_proband=1,
            with_intakes=0,
            proband_count=1,
        )
        drug_search_result = req("api/drug/search", q={"search_term": "Test"})
        _CONTEXT.update(
            study_id=study_data.study.id,
            interview_id=study_data.events[0].interviews[0].interview.id,
            proband_id=study_data.proband_ids[0],
            drug_id=drug_search_result["items"][0]["drug"]["id"],
        )
    return _CONTEXT


def _interview_started_days_ago(days: int) -> str:
    """An interview whose start lies `days` days in the past.

    Only one interview per proband per event is allowed, so every backdated
    interview gets its own event.
    """
    ctx = _context()
    event = req(
        f"api/study/{ctx['study_id']}/event",
        method="post",
        b={"name": f"PlausibilityEvent{len(_CONTEXT.get('backdated_events', []))}"},
    )
    _CONTEXT.setdefault("backdated_events", []).append(event["id"])
    start = datetime.datetime.now(datetime.timezone.utc).replace(
        tzinfo=None
    ) - datetime.timedelta(days=days)
    interview = req(
        f"api/study/{ctx['study_id']}/event/{event['id']}/interview",
        method="post",
        b={
            "proband_external_id": ctx["proband_id"],
            "proband_has_taken_meds": True,
            "interview_start_time_utc": start.isoformat(),
        },
    )
    return interview["id"]


def _payload(**overrides) -> Dict[str, Any]:
    """A valid intake payload, with the given fields replaced.

    Keeps the mutually exclusive date fields consistent, so a test can just say
    `intake_end_date=...` without also having to null out
    `intake_end_date_option`.
    """
    from medlogserver.model.intake import (
        AdministeredByDoctorAnswers,
        ConsumedMedsTodayAnswers,
        IntakeEndDateOption,
        IntakeRegularOrAsNeededAnswers,
        IntervalOfDailyDoseAnswers,
        SourceOfDrugInformationAnwers,
    )

    payload: Dict[str, Any] = {
        "drug_id": str(_context()["drug_id"]),
        "source_of_drug_information": SourceOfDrugInformationAnwers.DRUG_LEAFLET.value,
        "intake_start_date": _past(),
        "intake_end_date_option": IntakeEndDateOption.ONGOING.value,
        "administered_by_doctor": AdministeredByDoctorAnswers.PRESCRIBED.value,
        "intake_regular_or_as_needed": IntakeRegularOrAsNeededAnswers.REGULAR.value,
        "regular_intervall_of_daily_dose": IntervalOfDailyDoseAnswers.DAILY.value,
        "dose_per_day": 1,
        "consumed_meds_today": ConsumedMedsTodayAnswers.YES.value,
    }
    payload.update(overrides)

    if overrides.get("intake_start_date") is not None:
        payload.pop("intake_start_date_option", None)
    if overrides.get("intake_start_date_option") is not None:
        payload.pop("intake_start_date", None)
    if overrides.get("intake_end_date") is not None:
        payload.pop("intake_end_date_option", None)
    if overrides.get("intake_end_date_option") is not None:
        payload.pop("intake_end_date", None)
    if (
        overrides.get("intake_regular_or_as_needed")
        == IntakeRegularOrAsNeededAnswers.ASNEEDED.value
    ):
        payload["regular_intervall_of_daily_dose"] = None
    return payload


def _post(
    payload: Dict[str, Any],
    expected_http_code: int = None,
    interview_id: str = None,
) -> Dict[str, Any]:
    ctx = _context()
    interview_id = interview_id if interview_id is not None else ctx["interview_id"]
    return req(
        f"api/study/{ctx['study_id']}/interview/{interview_id}/intake",
        method="post",
        b=payload,
        expected_http_code=expected_http_code,
    )


def _patch(
    intake_id: str,
    payload: Dict[str, Any],
    expected_http_code: int = None,
    interview_id: str = None,
) -> Dict[str, Any]:
    ctx = _context()
    interview_id = interview_id if interview_id is not None else ctx["interview_id"]
    return req(
        f"api/study/{ctx['study_id']}/interview/{interview_id}/intake/{intake_id}",
        method="patch",
        b=payload,
        expected_http_code=expected_http_code,
    )


def _assert_rejected_by(response: Dict[str, Any], *allowed_rule_ids: str) -> None:
    """Assert the 422 body names one of the given rules and its fields."""
    detail = response.get("detail")
    assert isinstance(detail, dict), (
        f"Expected a structured plausibility detail, got {detail!r}. "
        "The frontend needs the rule and the fields to place a field-level hint."
    )
    assert detail["rule"] in allowed_rule_ids, (
        f"Expected one of {allowed_rule_ids}, got {detail['rule']!r}"
    )
    assert detail["fields"], "A plausibility error must name the fields it concerns"
    assert detail["msg"]
    # the date the rule compared against travels with the error, so the client
    # can build its own translated message
    assert set(detail["context"]) == {
        "today",
        "interview_date",
        "earliest_plausible_date",
    }
    if detail["reference"] is not None:
        assert detail["reference"] in detail["context"]
        assert detail["reference_date"] == detail["context"][detail["reference"]]
    else:
        assert detail["reference_date"] is None


# ── unit tests: the rules and the PATCH gating ─────────────────────────────


def _intake(**fields) -> SimpleNamespace:
    from medlogserver.model.intake_rules import INTAKE_PLAUSIBILITY_FIELDS

    return SimpleNamespace(**{f: fields.get(f) for f in INTAKE_PLAUSIBILITY_FIELDS})


def _earliest_plausible_date() -> str:
    """The configured floor, never a literal: it has been moved once already."""
    from medlogserver.model.intake_rules import EARLIEST_PLAUSIBLE_DATE

    return EARLIEST_PLAUSIBLE_DATE.isoformat()


def _reference(today: datetime.date, interview_date: datetime.date = None):
    """The two reference dates the rules use, see `IntakeReference`."""
    from medlogserver.model.intake_rules import IntakeReference

    return IntakeReference(
        today=today,
        interview_date=interview_date if interview_date is not None else today,
    )


def test_rule_ids_are_unique():
    from medlogserver.model.intake_rules import INTAKE_PLAUSIBILITY_RULES

    from medlogserver.model.intake_rules import IntakeReference

    rule_ids = [rule.id for rule in INTAKE_PLAUSIBILITY_RULES]
    assert len(rule_ids) == len(set(rule_ids))
    known_references = IntakeReference(
        today=datetime.date(2026, 6, 15), interview_date=datetime.date(2026, 6, 15)
    ).as_context()
    for rule in INTAKE_PLAUSIBILITY_RULES:
        assert rule.fields, f"rule {rule.id} must name the fields it concerns"
        assert rule.reference is None or rule.reference in known_references, (
            f"rule {rule.id} names an unknown reference date {rule.reference!r}"
        )


def test_interview_date_tolerance_is_symmetric():
    """A date one day off the interview date never breaks the "taken today" rules.

    The interview start time is stored as a naive UTC timestamp while
    interviewers work in local time, so the interview's local day can land one
    day on either side of the UTC day it is stored on.
    """
    from medlogserver.model.intake import ConsumedMedsTodayAnswers
    from medlogserver.model.intake_rules import validate_intake_plausibility

    interview_date = datetime.date(2026, 6, 15)
    # "today" is well past the interview, the case of an entry corrected later
    today = datetime.date(2026, 6, 30)
    for offset in (-1, 0, 1):
        day = interview_date + datetime.timedelta(days=offset)
        validate_intake_plausibility(
            _intake(
                intake_start_date=day,
                intake_end_date=day,
                consumed_meds_today=ConsumedMedsTodayAnswers.YES,
            ),
            reference=_reference(today=today, interview_date=interview_date),
        )


def test_tomorrow_is_a_future_date():
    """The "not in the future" rules have no tolerance (issue #338 review)."""
    import pytest

    from medlogserver.model.intake import (
        ConsumedMedsTodayAnswers,
        IntakeValidationError,
    )
    from medlogserver.model.intake_rules import validate_intake_plausibility

    today = datetime.date(2026, 6, 15)
    tomorrow = today + datetime.timedelta(days=1)

    with pytest.raises(IntakeValidationError) as start_err:
        validate_intake_plausibility(
            _intake(
                intake_start_date=tomorrow,
                consumed_meds_today=ConsumedMedsTodayAnswers.NO,
            ),
            reference=_reference(today=today),
        )
    assert start_err.value.rule_id == "start_date_in_future"

    with pytest.raises(IntakeValidationError) as end_err:
        validate_intake_plausibility(
            _intake(
                intake_start_date=today - datetime.timedelta(days=5),
                intake_end_date=tomorrow,
                consumed_meds_today=ConsumedMedsTodayAnswers.NO,
            ),
            reference=_reference(today=today),
        )
    assert end_err.value.rule_id == "end_date_in_future"

    # today itself stays allowed
    validate_intake_plausibility(
        _intake(
            intake_start_date=today,
            intake_end_date=today,
            consumed_meds_today=ConsumedMedsTodayAnswers.YES,
        ),
        reference=_reference(today=today),
    )


def test_taken_today_is_measured_against_the_interview_date():
    """An interview that ran days ago keeps its own "today".

    Reported in the review of issue #338: editing an older entry of an interview
    that was open for several days was rejected because "today" was read as the
    current date.
    """
    import pytest

    from medlogserver.model.intake import (
        ConsumedMedsTodayAnswers,
        IntakeValidationError,
    )
    from medlogserver.model.intake_rules import validate_intake_plausibility

    interview_date = datetime.date(2026, 6, 15)
    reference = _reference(
        today=datetime.date(2026, 6, 30), interview_date=interview_date
    )

    # the intake ended on the day of the interview: consistent with "taken today"
    validate_intake_plausibility(
        _intake(
            intake_start_date=datetime.date(2026, 6, 1),
            intake_end_date=interview_date,
            consumed_meds_today=ConsumedMedsTodayAnswers.YES,
        ),
        reference=reference,
    )

    # it ended well before the interview: still a contradiction
    with pytest.raises(IntakeValidationError) as err:
        validate_intake_plausibility(
            _intake(
                intake_start_date=datetime.date(2026, 6, 1),
                intake_end_date=datetime.date(2026, 6, 5),
                consumed_meds_today=ConsumedMedsTodayAnswers.YES,
            ),
            reference=reference,
        )
    assert err.value.rule_id == "consumed_today_with_past_end_date"
    # the interviewer cannot know which day is being compared against unless we
    # say it, so the date travels with the error, named and ready to be put into
    # a translated message
    assert err.value.reference == "interview_date"
    assert err.value.reference_date == "2026-06-15"
    assert err.value.context == {
        "today": "2026-06-30",
        "interview_date": "2026-06-15",
        "earliest_plausible_date": _earliest_plausible_date(),
    }
    assert "2026-06-15" in str(err.value)


def test_patch_gating_skips_rules_for_untouched_fields():
    """An intake that went stale stays editable in the fields it still needs.

    A record that was correct when it was entered can become contradictory just
    by time passing. Correcting an unrelated field weeks later must not be
    blocked by that.
    """
    import pytest

    from medlogserver.model.intake import (
        ConsumedMedsTodayAnswers,
        IntakeValidationError,
    )
    from medlogserver.model.intake_rules import validate_intake_plausibility

    reference = _reference(
        today=datetime.date(2026, 6, 15), interview_date=datetime.date(2026, 6, 10)
    )
    stale = _intake(
        intake_start_date=datetime.date(2026, 1, 1),
        intake_end_date=datetime.date(2026, 2, 1),
        consumed_meds_today=ConsumedMedsTodayAnswers.YES,
        dose_per_day=2,
    )

    # touching only the dose leaves the stale contradiction alone
    validate_intake_plausibility(
        stale, reference=reference, restrict_to_fields=["dose_per_day"]
    )

    # touching one of the conflicting fields does evaluate the rule, even though
    # the other half of the contradiction comes from the stored record
    with pytest.raises(IntakeValidationError) as err:
        validate_intake_plausibility(
            stale, reference=reference, restrict_to_fields=["intake_end_date"]
        )
    assert err.value.rule_id == "consumed_today_with_past_end_date"

    # and without a restriction every rule applies
    with pytest.raises(IntakeValidationError):
        validate_intake_plausibility(stale, reference=reference)


def test_rules_are_skipped_when_a_date_option_is_set():
    """An option carries no date, so there is nothing to order or compare."""
    from medlogserver.model.intake import ConsumedMedsTodayAnswers
    from medlogserver.model.intake_rules import validate_intake_plausibility

    validate_intake_plausibility(
        _intake(
            intake_start_date=None,  # intake_start_date_option is set instead
            intake_end_date=None,  # intake_end_date_option is set instead
            consumed_meds_today=ConsumedMedsTodayAnswers.YES,
            dose_per_day=1,
        ),
        reference=_reference(today=datetime.date(2026, 6, 15)),
    )


# ── rule 1: end date before start date ─────────────────────────────────────


def test_end_date_before_start_date_rejected_on_post():
    from medlogserver.model.intake import ConsumedMedsTodayAnswers

    response = _post(
        _payload(
            intake_start_date=_day_offset(-10),
            intake_end_date=_day_offset(-20),
            consumed_meds_today=ConsumedMedsTodayAnswers.NO.value,
        ),
        expected_http_code=422,
    )
    _assert_rejected_by(response, "end_date_before_start_date")


def test_end_date_before_start_date_rejected_on_patch():
    from medlogserver.model.intake import ConsumedMedsTodayAnswers

    intake = _post(
        _payload(
            intake_start_date=_day_offset(-10),
            intake_end_date=_day_offset(-5),
            consumed_meds_today=ConsumedMedsTodayAnswers.NO.value,
        )
    )
    # partial payload: only the end date is sent, the start date it contradicts
    # comes from the stored record
    response = _patch(
        intake["id"],
        {"intake_end_date": _day_offset(-20)},
        expected_http_code=422,
    )
    _assert_rejected_by(response, "end_date_before_start_date")


def test_start_and_end_on_the_same_day_accepted():
    from medlogserver.model.intake import ConsumedMedsTodayAnswers

    same_day = _day_offset(-5)
    _post(
        _payload(
            intake_start_date=same_day,
            intake_end_date=same_day,
            consumed_meds_today=ConsumedMedsTodayAnswers.NO.value,
        )
    )


# ── rule 2: start date in the future ───────────────────────────────────────


def test_start_date_in_future_rejected_on_post():
    response = _post(
        _payload(intake_start_date=_future()),
        expected_http_code=422,
    )
    # `consumed_meds_today` is Yes in the default payload, so either the plain
    # future-start rule or its "taken today" variant may catch this first
    _assert_rejected_by(
        response, "start_date_in_future", "consumed_today_with_future_start_date"
    )


def test_start_date_in_future_rejected_on_patch():
    intake = _post(_payload())
    response = _patch(
        intake["id"],
        {"intake_start_date": _future()},
        expected_http_code=422,
    )
    _assert_rejected_by(
        response, "start_date_in_future", "consumed_today_with_future_start_date"
    )


def test_tomorrow_is_rejected_as_a_future_start_date():
    """No tolerance on the future rules: tomorrow is a future date."""
    from medlogserver.model.intake import ConsumedMedsTodayAnswers

    response = _post(
        _payload(
            intake_start_date=_tomorrow(),
            consumed_meds_today=ConsumedMedsTodayAnswers.NO.value,
        ),
        expected_http_code=422,
    )
    _assert_rejected_by(response, "start_date_in_future")


def test_today_is_accepted_as_start_and_end_date():
    from medlogserver.model.intake import ConsumedMedsTodayAnswers

    today = _day_offset(0)
    _post(
        _payload(
            intake_start_date=today,
            intake_end_date=today,
            consumed_meds_today=ConsumedMedsTodayAnswers.YES.value,
        )
    )


# ── rule 3: end date in the future ─────────────────────────────────────────


def test_end_date_in_future_rejected_on_post():
    response = _post(
        _payload(intake_end_date=_future()),
        expected_http_code=422,
    )
    _assert_rejected_by(response, "end_date_in_future")


def test_end_date_in_future_rejected_on_patch():
    intake = _post(_payload())
    response = _patch(
        intake["id"],
        {"intake_end_date": _future()},
        expected_http_code=422,
    )
    _assert_rejected_by(response, "end_date_in_future")


def test_tomorrow_is_rejected_as_a_future_end_date():
    from medlogserver.model.intake import ConsumedMedsTodayAnswers

    response = _post(
        _payload(
            intake_end_date=_tomorrow(),
            consumed_meds_today=ConsumedMedsTodayAnswers.NO.value,
        ),
        expected_http_code=422,
    )
    _assert_rejected_by(response, "end_date_in_future")


# ── rule 4: "taken today" with an end date in the past ─────────────────────
#
# The originally reported case.


def test_consumed_today_with_past_end_date_rejected_on_post():
    from medlogserver.model.intake import ConsumedMedsTodayAnswers

    response = _post(
        _payload(
            intake_start_date=_past(),
            intake_end_date=_day_offset(-10),
            consumed_meds_today=ConsumedMedsTodayAnswers.YES.value,
        ),
        expected_http_code=422,
    )
    _assert_rejected_by(response, "consumed_today_with_past_end_date")


def test_consumed_today_with_past_end_date_rejected_on_patch():
    from medlogserver.model.intake import ConsumedMedsTodayAnswers

    intake = _post(
        _payload(consumed_meds_today=ConsumedMedsTodayAnswers.YES.value)
    )
    # partial payload: only the end date is sent, "taken today: Yes" is already
    # on the stored record
    response = _patch(
        intake["id"],
        {"intake_end_date": _day_offset(-10)},
        expected_http_code=422,
    )
    _assert_rejected_by(response, "consumed_today_with_past_end_date")


def test_consumed_today_set_to_yes_on_patch_against_stored_past_end_date():
    """The other half of the partial payload: only `consumed_meds_today` is sent."""
    from medlogserver.model.intake import ConsumedMedsTodayAnswers

    intake = _post(
        _payload(
            intake_start_date=_past(),
            intake_end_date=_day_offset(-10),
            consumed_meds_today=ConsumedMedsTodayAnswers.NO.value,
        )
    )
    response = _patch(
        intake["id"],
        {"consumed_meds_today": ConsumedMedsTodayAnswers.YES.value},
        expected_http_code=422,
    )
    _assert_rejected_by(response, "consumed_today_with_past_end_date")


# ── rule 5: "taken today" with a start date in the future ──────────────────


def test_consumed_today_with_future_start_date_rejected_on_post():
    from medlogserver.model.intake import ConsumedMedsTodayAnswers

    response = _post(
        _payload(
            intake_start_date=_future(),
            consumed_meds_today=ConsumedMedsTodayAnswers.YES.value,
        ),
        expected_http_code=422,
    )
    _assert_rejected_by(
        response, "consumed_today_with_future_start_date", "start_date_in_future"
    )


def test_consumed_today_with_future_start_date_rejected_on_patch():
    from medlogserver.model.intake import ConsumedMedsTodayAnswers

    intake = _post(
        _payload(consumed_meds_today=ConsumedMedsTodayAnswers.YES.value)
    )
    response = _patch(
        intake["id"],
        {"intake_start_date": _future()},
        expected_http_code=422,
    )
    _assert_rejected_by(
        response, "consumed_today_with_future_start_date", "start_date_in_future"
    )


# ── rule 6: negative doses ─────────────────────────────────────────────────
#
# `0` is *not* rejected: the interviewers use it as "the dose is unknown"
# (reported in the review of issue #338).


def test_negative_dose_per_day_rejected_on_post():
    response = _post(_payload(dose_per_day=-1), expected_http_code=422)
    _assert_rejected_by(response, "dose_per_day_negative")


def test_negative_dose_per_day_rejected_on_patch():
    intake = _post(_payload())
    response = _patch(intake["id"], {"dose_per_day": -1}, expected_http_code=422)
    _assert_rejected_by(response, "dose_per_day_negative")


def test_dose_per_day_zero_accepted():
    """`0` doses a day means "unknown", not an implausible value."""
    intake = _post(_payload(dose_per_day=0))
    assert intake["dose_per_day"] == 0
    updated = _patch(intake["id"], {"dose_per_day": 0})
    assert updated["dose_per_day"] == 0


def test_negative_as_needed_dose_unit_rejected_on_post():
    from medlogserver.model.intake import IntakeRegularOrAsNeededAnswers

    response = _post(
        _payload(
            intake_regular_or_as_needed=IntakeRegularOrAsNeededAnswers.ASNEEDED.value,
            as_needed_dose_unit=-1,
        ),
        expected_http_code=422,
    )
    _assert_rejected_by(response, "as_needed_dose_unit_negative")


def test_negative_as_needed_dose_unit_rejected_on_patch():
    from medlogserver.model.intake import IntakeRegularOrAsNeededAnswers

    intake = _post(
        _payload(
            intake_regular_or_as_needed=IntakeRegularOrAsNeededAnswers.ASNEEDED.value,
            as_needed_dose_unit=2,
        )
    )
    response = _patch(intake["id"], {"as_needed_dose_unit": -1}, expected_http_code=422)
    _assert_rejected_by(response, "as_needed_dose_unit_negative")


def test_as_needed_dose_unit_zero_accepted():
    from medlogserver.model.intake import IntakeRegularOrAsNeededAnswers

    intake = _post(
        _payload(
            intake_regular_or_as_needed=IntakeRegularOrAsNeededAnswers.ASNEEDED.value,
            as_needed_dose_unit=0,
        )
    )
    assert intake["as_needed_dose_unit"] == 0


def test_fractional_dose_still_accepted():
    """Rule 6 must not collide with the decimal doses from issue #337."""
    intake = _post(_payload(dose_per_day=0.25))
    assert intake["dose_per_day"] == 0.25


# ── rule 7: implausibly old dates ──────────────────────────────────────────


def test_implausibly_old_start_date_rejected_on_post():
    from medlogserver.model.intake import ConsumedMedsTodayAnswers

    response = _post(
        _payload(
            intake_start_date=_TYPO_DATE.isoformat(),
            consumed_meds_today=ConsumedMedsTodayAnswers.NO.value,
        ),
        expected_http_code=422,
    )
    _assert_rejected_by(response, "start_date_implausibly_old")


def test_implausibly_old_end_date_rejected_on_patch():
    from medlogserver.model.intake import ConsumedMedsTodayAnswers

    intake = _post(
        _payload(consumed_meds_today=ConsumedMedsTodayAnswers.NO.value)
    )
    response = _patch(
        intake["id"],
        {"intake_end_date": _TYPO_DATE.isoformat()},
        expected_http_code=422,
    )
    # the typo date is also before the start date, either rule is a correct
    # rejection
    _assert_rejected_by(
        response, "end_date_implausibly_old", "end_date_before_start_date"
    )


# ── the reference for "taken today" is the interview, not the server date ──
#
# Reported in the review of issue #338: an interview that stayed open for several
# days rejected every edit of an older entry, because "today" was read as the
# current date instead of the day the interview was held.


def test_taken_today_is_checked_against_the_interview_that_owns_the_intake():
    from medlogserver.model.intake import ConsumedMedsTodayAnswers

    interview_id = _interview_started_days_ago(5)
    # the intake ended on the day of that interview, five days ago
    intake = _post(
        _payload(
            intake_start_date=_day_offset(-30),
            intake_end_date=_day_offset(-5),
            consumed_meds_today=ConsumedMedsTodayAnswers.YES.value,
        ),
        interview_id=interview_id,
    )
    # and editing it days later is still allowed
    updated = _patch(
        intake["id"],
        {"intake_end_date": _day_offset(-5)},
        interview_id=interview_id,
    )
    assert updated["intake_end_date"] == _day_offset(-5)


def test_taken_today_still_rejected_before_the_interview_date():
    from medlogserver.model.intake import ConsumedMedsTodayAnswers

    interview_id = _interview_started_days_ago(5)
    response = _post(
        _payload(
            intake_start_date=_day_offset(-30),
            intake_end_date=_day_offset(-15),
            consumed_meds_today=ConsumedMedsTodayAnswers.YES.value,
        ),
        expected_http_code=422,
        interview_id=interview_id,
    )
    _assert_rejected_by(response, "consumed_today_with_past_end_date")
    # the interview date is reported as the reference of the broken rule, so the
    # client can name the day the answer was checked against in its own language
    assert response["detail"]["reference"] == "interview_date"
    assert response["detail"]["reference_date"] == _day_offset(-5)
    assert _day_offset(-5) in response["detail"]["msg"]


def test_implausibly_old_date_reports_the_floor_as_reference():
    """The client can render "before {reference_date}" for this rule too."""
    from medlogserver.model.intake import ConsumedMedsTodayAnswers

    response = _post(
        _payload(
            intake_start_date=_TYPO_DATE.isoformat(),
            consumed_meds_today=ConsumedMedsTodayAnswers.NO.value,
        ),
        expected_http_code=422,
    )
    _assert_rejected_by(response, "start_date_implausibly_old")
    assert response["detail"]["reference"] == "earliest_plausible_date"
    assert response["detail"]["reference_date"] == _earliest_plausible_date()


# ── explicitly allowed combinations ────────────────────────────────────────


def test_not_consumed_today_with_past_end_date_accepted():
    from medlogserver.model.intake import ConsumedMedsTodayAnswers

    for answer in (ConsumedMedsTodayAnswers.NO, ConsumedMedsTodayAnswers.UNKNOWN):
        _post(
            _payload(
                intake_start_date=_past(),
                intake_end_date=_day_offset(-10),
                consumed_meds_today=answer.value,
            )
        )


def test_ongoing_end_date_option_accepted_with_any_consumed_answer():
    from medlogserver.model.intake import ConsumedMedsTodayAnswers, IntakeEndDateOption

    for answer in (
        ConsumedMedsTodayAnswers.YES,
        ConsumedMedsTodayAnswers.NO,
        ConsumedMedsTodayAnswers.UNKNOWN,
    ):
        _post(
            _payload(
                intake_end_date_option=IntakeEndDateOption.ONGOING.value,
                consumed_meds_today=answer.value,
            )
        )


def test_start_date_option_accepted_with_any_end_date():
    """No exact start date means rules 1, 2 and 5 have nothing to compare."""
    from medlogserver.model.intake import (
        ConsumedMedsTodayAnswers,
        IntakeStartDateOption,
    )

    for option in (
        IntakeStartDateOption.AT_LEAST_12_MONTHS,
        IntakeStartDateOption.UNKNOWN,
    ):
        _post(
            _payload(
                intake_start_date_option=option.value,
                intake_end_date=_day_offset(-10),
                consumed_meds_today=ConsumedMedsTodayAnswers.NO.value,
            )
        )


def test_unrelated_patch_on_valid_intake_still_accepted():
    intake = _post(_payload())
    updated = _patch(intake["id"], {"dose_per_day": 3})
    assert updated["dose_per_day"] == 3
