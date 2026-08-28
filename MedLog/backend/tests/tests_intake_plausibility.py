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
# The rules compare against the server's *UTC* date with one day of tolerance in
# both directions. The test machine's local date can differ from the server's
# UTC date, so every offset used here is comfortably outside that window.

_FAR_FUTURE_DAYS = 10
_FAR_PAST_DAYS = 30
# A typo like "0202" instead of "2020", the case the floor is meant to catch.
_TYPO_DATE = datetime.date(202, 1, 1)


def _day_offset(days: int) -> str:
    return (datetime.date.today() + datetime.timedelta(days=days)).isoformat()


def _future() -> str:
    return _day_offset(_FAR_FUTURE_DAYS)


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
            drug_id=drug_search_result["items"][0]["drug"]["id"],
        )
    return _CONTEXT


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


def _post(payload: Dict[str, Any], expected_http_code: int = None) -> Dict[str, Any]:
    ctx = _context()
    return req(
        f"api/study/{ctx['study_id']}/interview/{ctx['interview_id']}/intake",
        method="post",
        b=payload,
        expected_http_code=expected_http_code,
    )


def _patch(
    intake_id: str, payload: Dict[str, Any], expected_http_code: int = None
) -> Dict[str, Any]:
    ctx = _context()
    return req(
        f"api/study/{ctx['study_id']}/interview/{ctx['interview_id']}/intake/{intake_id}",
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


# ── unit tests: the rules and the PATCH gating ─────────────────────────────


def _intake(**fields) -> SimpleNamespace:
    from medlogserver.model.intake_rules import INTAKE_PLAUSIBILITY_FIELDS

    return SimpleNamespace(**{f: fields.get(f) for f in INTAKE_PLAUSIBILITY_FIELDS})


def test_rule_ids_are_unique():
    from medlogserver.model.intake_rules import INTAKE_PLAUSIBILITY_RULES

    rule_ids = [rule.id for rule in INTAKE_PLAUSIBILITY_RULES]
    assert len(rule_ids) == len(set(rule_ids))
    for rule in INTAKE_PLAUSIBILITY_RULES:
        assert rule.fields, f"rule {rule.id} must name the fields it concerns"


def test_reference_date_tolerance_is_symmetric():
    """A date one day off "today" is never rejected.

    Timestamps are stored as naive UTC while interviewers work in local time, so
    around midnight a correctly entered date can land one day on either side of
    the server's UTC date.
    """
    from medlogserver.model.intake import ConsumedMedsTodayAnswers
    from medlogserver.model.intake_rules import validate_intake_plausibility

    reference = datetime.date(2026, 6, 15)
    for offset in (-1, 0, 1):
        day = reference + datetime.timedelta(days=offset)
        validate_intake_plausibility(
            _intake(
                intake_start_date=day,
                intake_end_date=day,
                consumed_meds_today=ConsumedMedsTodayAnswers.YES,
            ),
            reference_date=reference,
        )


def test_patch_gating_skips_rules_for_untouched_fields():
    """An intake that went stale stays editable in the fields it still needs.

    With the server date as reference, a record that was correct when it was
    entered can become contradictory just by time passing. Correcting an
    unrelated field weeks later must not be blocked by that.
    """
    import pytest

    from medlogserver.model.intake import (
        ConsumedMedsTodayAnswers,
        IntakeValidationError,
    )
    from medlogserver.model.intake_rules import validate_intake_plausibility

    reference = datetime.date(2026, 6, 15)
    stale = _intake(
        intake_start_date=datetime.date(2026, 1, 1),
        intake_end_date=datetime.date(2026, 2, 1),
        consumed_meds_today=ConsumedMedsTodayAnswers.YES,
        dose_per_day=2,
    )

    # touching only the dose leaves the stale contradiction alone
    validate_intake_plausibility(
        stale, reference_date=reference, restrict_to_fields=["dose_per_day"]
    )

    # touching one of the conflicting fields does evaluate the rule, even though
    # the other half of the contradiction comes from the stored record
    with pytest.raises(IntakeValidationError) as err:
        validate_intake_plausibility(
            stale, reference_date=reference, restrict_to_fields=["intake_end_date"]
        )
    assert err.value.rule_id == "consumed_today_with_past_end_date"

    # and without a restriction every rule applies
    with pytest.raises(IntakeValidationError):
        validate_intake_plausibility(stale, reference_date=reference)


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
        reference_date=datetime.date(2026, 6, 15),
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


# ── rule 6: non-positive doses ─────────────────────────────────────────────


def test_non_positive_dose_per_day_rejected_on_post():
    for dose in (0, -1):
        response = _post(_payload(dose_per_day=dose), expected_http_code=422)
        _assert_rejected_by(response, "dose_per_day_not_positive")


def test_non_positive_dose_per_day_rejected_on_patch():
    intake = _post(_payload())
    response = _patch(intake["id"], {"dose_per_day": 0}, expected_http_code=422)
    _assert_rejected_by(response, "dose_per_day_not_positive")


def test_non_positive_as_needed_dose_unit_rejected_on_post():
    from medlogserver.model.intake import IntakeRegularOrAsNeededAnswers

    response = _post(
        _payload(
            intake_regular_or_as_needed=IntakeRegularOrAsNeededAnswers.ASNEEDED.value,
            as_needed_dose_unit=0,
        ),
        expected_http_code=422,
    )
    _assert_rejected_by(response, "as_needed_dose_unit_not_positive")


def test_non_positive_as_needed_dose_unit_rejected_on_patch():
    from medlogserver.model.intake import IntakeRegularOrAsNeededAnswers

    intake = _post(
        _payload(
            intake_regular_or_as_needed=IntakeRegularOrAsNeededAnswers.ASNEEDED.value,
            as_needed_dose_unit=2,
        )
    )
    response = _patch(
        intake["id"], {"as_needed_dose_unit": 0}, expected_http_code=422
    )
    _assert_rejected_by(response, "as_needed_dose_unit_not_positive")


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
