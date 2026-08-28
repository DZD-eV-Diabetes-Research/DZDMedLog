"""Plausibility rules for intake records.

This module is the single place that collects every "this combination of values
cannot be true" check for an intake. The mutual-exclusivity / field-presence
checks stay in the pydantic validators of `IntakeUpdate`, this module only deals
with the *plausibility of the values*.

Adding a rule means adding one entry to `INTAKE_PLAUSIBILITY_RULES`, nothing
else. The rules are evaluated by `IntakeCRUD` (see `medlogserver/db/intake.py`),
which is the choke point every write goes through, so POST, PATCH and any future
writer are covered without repeating the checks per route.

Each rule carries the fields it concerns. That serves two purposes:

* the API can tell the client which fields to highlight, instead of a generic
  "invalid intake"
* on PATCH a rule is only enforced when the request actually touched one of its
  fields (see `validate_intake_plausibility`)
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Iterable, Optional, Tuple

from medlogserver.model.intake import (
    ConsumedMedsTodayAnswers,
    IntakeValidationError,
)


# All checks are done against the server's current UTC date ("now").
#
# Timestamps are stored as naive UTC while interviewers work in local time, so a
# date the interviewer legitimately entered as "today" can be one day ahead of
# (or behind) the server's UTC date around midnight. Every comparison against
# the reference date therefore gets one day of slack, in both directions. The
# frontend blocks future dates in the date pickers; this tolerance only exists so
# the backend does not reject correct entries because of a timezone offset.
REFERENCE_DATE_TOLERANCE = timedelta(days=1)

# Dates before this are typos, not data (e.g. year "0202" instead of "2020").
# There is no birth date in the system, so a fixed floor is the only option.
EARLIEST_PLAUSIBLE_DATE = date(1900, 1, 1)


def current_reference_date() -> date:
    """The "today" every rule compares against."""
    return datetime.now(timezone.utc).date()


@dataclass(frozen=True)
class IntakeRule:
    id: str
    """Stable identifier, sent to the client so it can map the error to a hint."""

    fields: Tuple[str, ...]
    """Intake fields this rule is about. Used for the client-side field hint and
    for deciding whether a PATCH has to be checked against this rule."""

    message: str
    """Human readable explanation of what is wrong."""

    is_violated: Callable[[Any, date], bool]
    """Takes the (merged) intake and the reference date, returns True if the
    intake breaks this rule."""


def _end_date_before_start_date(intake: Any, reference_date: date) -> bool:
    start = intake.intake_start_date
    end = intake.intake_end_date
    # Equal dates are a valid one-day intake. If an option is set instead of a
    # date, the corresponding date is None and there is nothing to order.
    return start is not None and end is not None and end < start


def _start_date_in_future(intake: Any, reference_date: date) -> bool:
    start = intake.intake_start_date
    return start is not None and start > reference_date + REFERENCE_DATE_TOLERANCE


def _end_date_in_future(intake: Any, reference_date: date) -> bool:
    end = intake.intake_end_date
    return end is not None and end > reference_date + REFERENCE_DATE_TOLERANCE


def _consumed_today_with_past_end_date(intake: Any, reference_date: date) -> bool:
    end = intake.intake_end_date
    return (
        intake.consumed_meds_today == ConsumedMedsTodayAnswers.YES
        and end is not None
        and end < reference_date - REFERENCE_DATE_TOLERANCE
    )


def _consumed_today_with_future_start_date(intake: Any, reference_date: date) -> bool:
    start = intake.intake_start_date
    return (
        intake.consumed_meds_today == ConsumedMedsTodayAnswers.YES
        and start is not None
        and start > reference_date + REFERENCE_DATE_TOLERANCE
    )


def _dose_per_day_not_positive(intake: Any, reference_date: date) -> bool:
    dose = intake.dose_per_day
    return dose is not None and dose <= 0


def _as_needed_dose_unit_not_positive(intake: Any, reference_date: date) -> bool:
    dose = intake.as_needed_dose_unit
    return dose is not None and dose <= 0


def _start_date_implausibly_old(intake: Any, reference_date: date) -> bool:
    start = intake.intake_start_date
    return start is not None and start < EARLIEST_PLAUSIBLE_DATE


def _end_date_implausibly_old(intake: Any, reference_date: date) -> bool:
    end = intake.intake_end_date
    return end is not None and end < EARLIEST_PLAUSIBLE_DATE


INTAKE_PLAUSIBILITY_RULES: Tuple[IntakeRule, ...] = (
    IntakeRule(
        id="end_date_before_start_date",
        fields=("intake_start_date", "intake_end_date"),
        message=(
            "'intake_end_date' must not be before 'intake_start_date'. "
            "Start and end on the same day are allowed."
        ),
        is_violated=_end_date_before_start_date,
    ),
    IntakeRule(
        id="start_date_in_future",
        fields=("intake_start_date",),
        message=(
            "'intake_start_date' must not be in the future. An intake that has "
            "not begun yet cannot be recorded."
        ),
        is_violated=_start_date_in_future,
    ),
    IntakeRule(
        id="end_date_in_future",
        fields=("intake_end_date",),
        message="'intake_end_date' must not be in the future.",
        is_violated=_end_date_in_future,
    ),
    IntakeRule(
        id="consumed_today_with_past_end_date",
        fields=("consumed_meds_today", "intake_end_date"),
        message=(
            "'consumed_meds_today' cannot be 'Yes' when 'intake_end_date' is in "
            "the past. The intake had already ended."
        ),
        is_violated=_consumed_today_with_past_end_date,
    ),
    IntakeRule(
        id="consumed_today_with_future_start_date",
        fields=("consumed_meds_today", "intake_start_date"),
        message=(
            "'consumed_meds_today' cannot be 'Yes' when 'intake_start_date' is "
            "in the future. The intake has not begun yet."
        ),
        is_violated=_consumed_today_with_future_start_date,
    ),
    IntakeRule(
        id="dose_per_day_not_positive",
        fields=("dose_per_day",),
        message="'dose_per_day' must be greater than 0.",
        is_violated=_dose_per_day_not_positive,
    ),
    IntakeRule(
        id="as_needed_dose_unit_not_positive",
        fields=("as_needed_dose_unit",),
        message="'as_needed_dose_unit' must be greater than 0.",
        is_violated=_as_needed_dose_unit_not_positive,
    ),
    IntakeRule(
        id="start_date_implausibly_old",
        fields=("intake_start_date",),
        message=(
            f"'intake_start_date' must not be before "
            f"{EARLIEST_PLAUSIBLE_DATE.isoformat()}."
        ),
        is_violated=_start_date_implausibly_old,
    ),
    IntakeRule(
        id="end_date_implausibly_old",
        fields=("intake_end_date",),
        message=(
            f"'intake_end_date' must not be before "
            f"{EARLIEST_PLAUSIBLE_DATE.isoformat()}."
        ),
        is_violated=_end_date_implausibly_old,
    ),
)


# Every field any rule looks at. Used to build the merged view of an intake for
# a PATCH without having to touch the ORM object.
INTAKE_PLAUSIBILITY_FIELDS: Tuple[str, ...] = tuple(
    dict.fromkeys(field for rule in INTAKE_PLAUSIBILITY_RULES for field in rule.fields)
)


def validate_intake_plausibility(
    intake: Any,
    reference_date: Optional[date] = None,
    restrict_to_fields: Optional[Iterable[str]] = None,
) -> None:
    """Raise `IntakeValidationError` for the first rule the intake violates.

    Args:
        intake: anything carrying the intake fields as attributes. For a PATCH
            this must be the *merged* record (database row + payload), not the
            payload alone, otherwise a partial update slips through.
        reference_date: the "today" to compare against. Defaults to the server's
            current UTC date.
        restrict_to_fields: when given, only rules that concern at least one of
            these fields are enforced.

            This is what a PATCH passes in, with the fields the request actually
            sent. Without it, editing an unrelated field of an older record
            (e.g. fixing a typo in the dose weeks later) would be rejected
            because the record's own dates have meanwhile moved into the past
            relative to "now". The partial-payload case still gets caught: a
            PATCH sending only `intake_end_date` touches a field of the ordering
            and the "taken today" rules, so both are evaluated against the merged
            record.
    """
    if reference_date is None:
        reference_date = current_reference_date()
    restricted = set(restrict_to_fields) if restrict_to_fields is not None else None

    for rule in INTAKE_PLAUSIBILITY_RULES:
        if restricted is not None and not restricted.intersection(rule.fields):
            continue
        if rule.is_violated(intake, reference_date):
            raise IntakeValidationError(
                rule.message, rule_id=rule.id, fields=rule.fields
            )
