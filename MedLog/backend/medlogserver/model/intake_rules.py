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

Two different reference dates are used, see `IntakeReference`.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Dict, Iterable, Optional, Tuple

from medlogserver.model.intake import (
    ConsumedMedsTodayAnswers,
    IntakeValidationError,
)


# Tolerance for the comparisons against the interview date.
#
# The interview start time is stored as a naive UTC timestamp while interviewers
# work in local time, so the interview's local day can be one day ahead of (or
# behind) the UTC day the timestamp falls on. The interview-relative rules
# therefore get one day of slack in both directions.
#
# The "not in the future" rules deliberately have *no* tolerance: tomorrow is a
# future date and gets rejected (issue #338 review).
INTERVIEW_DATE_TOLERANCE = timedelta(days=1)

# Dates before this are typos, not data (e.g. year "0202" instead of "2020").
# There is no birth date in the system, so a fixed floor is the only option.
EARLIEST_PLAUSIBLE_DATE = date(1950, 1, 1)


# The dates a rule can compare against. A violation reports which one it used
# and its value, so a client can build a translated message ("... liegt nach dem
# {reference_date}") without having to know the semantics of every single rule.
REFERENCE_TODAY = "today"
REFERENCE_INTERVIEW_DATE = "interview_date"
REFERENCE_EARLIEST_PLAUSIBLE_DATE = "earliest_plausible_date"


def current_utc_date() -> date:
    """The server's current UTC date."""
    return datetime.now(timezone.utc).date()


@dataclass(frozen=True)
class IntakeReference:
    """The dates the rules compare against.

    `today` is the server's current UTC date. It is the upper bound for "this
    date is in the future": nothing can be recorded for a day that has not
    happened yet, no matter when the interview was started.

    `interview_date` is the day the parent interview was started. It is what
    "today" means in the question "was this medication taken today?", which the
    proband answered during the interview. Using the server date there would
    retroactively invalidate correct answers as soon as an interview stays open
    across midnight or an entry is edited on a later day, which is what the
    review of issue #338 reported.

    Because the interview date is the reference for those rules, the API hands
    both dates to the client (see `as_context()`), so the error message can name
    the day the check is against instead of leaving the interviewer guessing.
    """

    today: date
    interview_date: date

    @classmethod
    def for_interview_start(
        cls,
        interview_start_time_utc: Optional[datetime] = None,
        today: Optional[date] = None,
    ) -> "IntakeReference":
        """Build the reference from an interview's (naive UTC) start timestamp.

        Falls back to the current date when the interview or its start time is
        unavailable, so a missing interview can never turn into a crash inside a
        validation rule.
        """
        today = today if today is not None else current_utc_date()
        interview_date = (
            interview_start_time_utc.date()
            if interview_start_time_utc is not None
            else today
        )
        return cls(today=today, interview_date=interview_date)

    def as_context(self) -> Dict[str, str]:
        """Every date a rule may refer to, as ISO strings.

        Sent to the client as the `context` of a violation and used to fill the
        placeholders in the rule messages.
        """
        return {
            REFERENCE_TODAY: self.today.isoformat(),
            REFERENCE_INTERVIEW_DATE: self.interview_date.isoformat(),
            REFERENCE_EARLIEST_PLAUSIBLE_DATE: EARLIEST_PLAUSIBLE_DATE.isoformat(),
        }


@dataclass(frozen=True)
class IntakeRule:
    id: str
    """Stable identifier, sent to the client so it can map the error to a hint."""

    fields: Tuple[str, ...]
    """Intake fields this rule is about. Used for the client-side field hint and
    for deciding whether a PATCH has to be checked against this rule."""

    message: str
    """Human readable explanation of what is wrong. May contain the `{today}`,
    `{interview_date}` and `{earliest_plausible_date}` placeholders, filled from
    the reference dates."""

    is_violated: Callable[[Any, IntakeReference], bool]
    """Takes the (merged) intake and the reference dates, returns True if the
    intake breaks this rule."""

    reference: Optional[str] = None
    """Which reference date this rule compares against, if any. Reported with the
    violation (`reference` / `reference_date`) so a client can put the date into
    its own translated message."""


def _end_date_before_start_date(intake: Any, reference: IntakeReference) -> bool:
    start = intake.intake_start_date
    end = intake.intake_end_date
    # Equal dates are a valid one-day intake. If an option is set instead of a
    # date, the corresponding date is None and there is nothing to order.
    return start is not None and end is not None and end < start


def _start_date_in_future(intake: Any, reference: IntakeReference) -> bool:
    start = intake.intake_start_date
    return start is not None and start > reference.today


def _end_date_in_future(intake: Any, reference: IntakeReference) -> bool:
    end = intake.intake_end_date
    return end is not None and end > reference.today


def _consumed_today_with_past_end_date(intake: Any, reference: IntakeReference) -> bool:
    end = intake.intake_end_date
    return (
        intake.consumed_meds_today == ConsumedMedsTodayAnswers.YES
        and end is not None
        and end < reference.interview_date - INTERVIEW_DATE_TOLERANCE
    )


def _consumed_today_with_future_start_date(
    intake: Any, reference: IntakeReference
) -> bool:
    start = intake.intake_start_date
    return (
        intake.consumed_meds_today == ConsumedMedsTodayAnswers.YES
        and start is not None
        and start > reference.interview_date + INTERVIEW_DATE_TOLERANCE
    )


def _dose_per_day_negative(intake: Any, reference: IntakeReference) -> bool:
    dose = intake.dose_per_day
    return dose is not None and dose < 0


def _as_needed_dose_unit_negative(intake: Any, reference: IntakeReference) -> bool:
    dose = intake.as_needed_dose_unit
    return dose is not None and dose < 0


def _start_date_implausibly_old(intake: Any, reference: IntakeReference) -> bool:
    start = intake.intake_start_date
    return start is not None and start < EARLIEST_PLAUSIBLE_DATE


def _end_date_implausibly_old(intake: Any, reference: IntakeReference) -> bool:
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
            "'intake_start_date' must not be after {today}, the current date. "
            "An intake that has not begun yet cannot be recorded."
        ),
        is_violated=_start_date_in_future,
        reference=REFERENCE_TODAY,
    ),
    IntakeRule(
        id="end_date_in_future",
        fields=("intake_end_date",),
        message="'intake_end_date' must not be after {today}, the current date.",
        is_violated=_end_date_in_future,
        reference=REFERENCE_TODAY,
    ),
    IntakeRule(
        id="consumed_today_with_past_end_date",
        fields=("consumed_meds_today", "intake_end_date"),
        message=(
            "'consumed_meds_today' is 'Yes', but 'intake_end_date' is before "
            "{interview_date}, the day this interview was started. 'Today' refers "
            "to the day of the interview, and an intake that had already ended "
            "cannot have been taken on that day."
        ),
        is_violated=_consumed_today_with_past_end_date,
        reference=REFERENCE_INTERVIEW_DATE,
    ),
    IntakeRule(
        id="consumed_today_with_future_start_date",
        fields=("consumed_meds_today", "intake_start_date"),
        message=(
            "'consumed_meds_today' is 'Yes', but 'intake_start_date' is after "
            "{interview_date}, the day this interview was started. 'Today' refers "
            "to the day of the interview, and an intake that had not begun yet "
            "cannot have been taken on that day."
        ),
        is_violated=_consumed_today_with_future_start_date,
        reference=REFERENCE_INTERVIEW_DATE,
    ),
    IntakeRule(
        id="dose_per_day_negative",
        fields=("dose_per_day",),
        message=(
            "'dose_per_day' must not be negative. 0 is allowed and is used when "
            "the daily dose is unknown."
        ),
        is_violated=_dose_per_day_negative,
    ),
    IntakeRule(
        id="as_needed_dose_unit_negative",
        fields=("as_needed_dose_unit",),
        message=(
            "'as_needed_dose_unit' must not be negative. 0 is allowed and is used "
            "when the dose is unknown."
        ),
        is_violated=_as_needed_dose_unit_negative,
    ),
    IntakeRule(
        id="start_date_implausibly_old",
        fields=("intake_start_date",),
        message="'intake_start_date' must not be before {earliest_plausible_date}.",
        is_violated=_start_date_implausibly_old,
        reference=REFERENCE_EARLIEST_PLAUSIBLE_DATE,
    ),
    IntakeRule(
        id="end_date_implausibly_old",
        fields=("intake_end_date",),
        message="'intake_end_date' must not be before {earliest_plausible_date}.",
        is_violated=_end_date_implausibly_old,
        reference=REFERENCE_EARLIEST_PLAUSIBLE_DATE,
    ),
)


# Every field any rule looks at. Used to build the merged view of an intake for
# a PATCH without having to touch the ORM object.
INTAKE_PLAUSIBILITY_FIELDS: Tuple[str, ...] = tuple(
    dict.fromkeys(field for rule in INTAKE_PLAUSIBILITY_RULES for field in rule.fields)
)


def validate_intake_plausibility(
    intake: Any,
    reference: Optional[IntakeReference] = None,
    restrict_to_fields: Optional[Iterable[str]] = None,
) -> None:
    """Raise `IntakeValidationError` for the first rule the intake violates.

    Args:
        intake: anything carrying the intake fields as attributes. For a PATCH
            this must be the *merged* record (database row + payload), not the
            payload alone, otherwise a partial update slips through.
        reference: the dates to compare against, see `IntakeReference`. Defaults
            to the current UTC date for both, i.e. to the behaviour of an
            interview started today.
        restrict_to_fields: when given, only rules that concern at least one of
            these fields are enforced.

            This is what a PATCH passes in, with the fields the request actually
            sent. Without it, editing an unrelated field of an older record
            (e.g. fixing a typo in the dose weeks later) would be rejected
            because the record's own dates have meanwhile moved into the past.
            The partial-payload case still gets caught: a PATCH sending only
            `intake_end_date` touches a field of the ordering and the "taken
            today" rules, so both are evaluated against the merged record.
    """
    if reference is None:
        reference = IntakeReference.for_interview_start()
    restricted = set(restrict_to_fields) if restrict_to_fields is not None else None
    context = reference.as_context()

    for rule in INTAKE_PLAUSIBILITY_RULES:
        if restricted is not None and not restricted.intersection(rule.fields):
            continue
        if rule.is_violated(intake, reference):
            raise IntakeValidationError(
                rule.message.format(**context),
                rule_id=rule.id,
                fields=rule.fields,
                reference=rule.reference,
                reference_date=context.get(rule.reference) if rule.reference else None,
                context=context,
            )
