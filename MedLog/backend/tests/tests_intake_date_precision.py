"""Imprecise intake dates: month only / year only.

See https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues/392

Covered:

* the period helpers (earliest / latest day, reduced precision format)
* the plausibility rules with imprecise and mixed precision dates, as unit tests
* the API: defaults, normalization to the start of the period, the
  "precision only with a date" rules, POST and PATCH
* the export: reduced precision value, `_precision`, `_earliest`, `_latest`,
  validated against the export schemas
* the migration on the database backend of the test run (SQLite or Postgres)
"""

import asyncio
import csv
import datetime
import io
import json
import uuid
from typing import Any, Dict, Optional

import pytest

from utils import req, create_test_study, TestDataContainerStudy
from tests_export_performance import session_db, _export_layout, _run_export
from tests_intake_plausibility import (
    _assert_rejected_by,
    _intake,
    _patch,
    _payload,
    _post,
    _reference,
    _today,
)


# A fixed "today" for the unit tests, so month and year boundaries are known.
_UNIT_TODAY = datetime.date(2026, 10, 9)


def _first_of_next_month(day: datetime.date) -> datetime.date:
    return (day.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)


# ── period helpers ─────────────────────────────────────────────────────────


def test_period_helpers():
    from medlogserver.model.intake import (
        IntakeDatePrecision as P,
        format_intake_date,
        intake_date_earliest,
        intake_date_latest,
    )

    day = datetime.date(2024, 3, 10)
    expected = {
        # precision: (formatted, earliest, latest)
        P.DAY: ("2024-03-10", day, day),
        P.MONTH: ("2024-03", datetime.date(2024, 3, 1), datetime.date(2024, 3, 31)),
        P.YEAR: ("2024", datetime.date(2024, 1, 1), datetime.date(2024, 12, 31)),
        # no precision: an exact day, as every date before #392
        None: ("2024-03-10", day, day),
    }
    for precision, (formatted, earliest, latest) in expected.items():
        assert format_intake_date(day, precision) == formatted
        assert intake_date_earliest(day, precision) == earliest
        assert intake_date_latest(day, precision) == latest

    # month lengths
    assert intake_date_latest(datetime.date(2024, 2, 1), P.MONTH) == datetime.date(2024, 2, 29)
    assert intake_date_latest(datetime.date(2023, 2, 1), P.MONTH) == datetime.date(2023, 2, 28)
    assert intake_date_latest(datetime.date(2024, 12, 1), P.MONTH) == datetime.date(2024, 12, 31)

    for helper in (format_intake_date, intake_date_earliest, intake_date_latest):
        assert helper(None, P.MONTH) is None


# ── model validation ───────────────────────────────────────────────────────


def _create_model(**fields):
    from medlogserver.model.intake import IntakeCreate

    return IntakeCreate(
        drug_id=uuid.uuid4(),
        interview_id=uuid.uuid4(),
        consumed_meds_today="Yes",
        **fields,
    )


def test_model_normalizes_dates_to_start_of_period():
    from medlogserver.model.intake import IntakeDatePrecision as P

    intake = _create_model(
        intake_start_date="2024-03-15",
        intake_start_date_precision="year",
        intake_end_date="2025-07-20",
        intake_end_date_precision="month",
    )
    assert intake.intake_start_date == datetime.date(2024, 1, 1)
    assert intake.intake_start_date_precision == P.YEAR
    assert intake.intake_end_date == datetime.date(2025, 7, 1)
    assert intake.intake_end_date_precision == P.MONTH


def test_model_precision_defaults_to_day_and_is_null_for_options():
    from medlogserver.model.intake import IntakeDatePrecision as P

    intake = _create_model(
        intake_start_date="2024-03-15",
        intake_start_date_precision=None,
        intake_end_date=None,
    )
    assert intake.intake_start_date == datetime.date(2024, 3, 15)
    assert intake.intake_start_date_precision == P.DAY
    # the end date falls back to the option ONGOING, which has no precision
    assert intake.intake_end_date_option is not None
    assert intake.intake_end_date_precision is None

    intake = _create_model(intake_start_date_option="unknown")
    assert intake.intake_start_date_precision is None


def test_model_rejects_precision_with_option_or_without_date():
    from pydantic import ValidationError
    from medlogserver.model.intake import IntakeUpdate

    with pytest.raises(ValidationError, match="must be null when 'intake_start_date_option'"):
        _create_model(intake_start_date_option="unknown", intake_start_date_precision="day")
    with pytest.raises(ValidationError, match="must be null when 'intake_end_date_option'"):
        _create_model(
            intake_start_date="2024-03-15",
            intake_end_date_option="ongoing",
            intake_end_date_precision="month",
        )
    with pytest.raises(ValidationError, match="can only be sent together with"):
        IntakeUpdate(intake_end_date_precision="month")
    with pytest.raises(ValidationError):
        _create_model(intake_start_date="2024-03-15", intake_start_date_precision="week")


# ── plausibility rules, unit tests ─────────────────────────────────────────


def _violated_rule(reference=None, **fields) -> Optional[str]:
    from medlogserver.model.intake import IntakeValidationError
    from medlogserver.model.intake_rules import validate_intake_plausibility

    try:
        validate_intake_plausibility(
            _intake(**fields),
            reference=reference if reference is not None else _reference(_UNIT_TODAY),
        )
    except IntakeValidationError as e:
        return e.rule_id
    return None


def test_end_date_before_start_date_with_imprecise_dates():
    from medlogserver.model.intake import IntakeDatePrecision as P

    start_day = dict(
        intake_start_date=datetime.date(2024, 3, 20),
        intake_start_date_precision=P.DAY,
    )
    # end "March 2024" can be on or after the 20th
    assert _violated_rule(
        **start_day,
        intake_end_date=datetime.date(2024, 3, 1),
        intake_end_date_precision=P.MONTH,
    ) is None
    # end "February 2024" cannot
    assert _violated_rule(
        **start_day,
        intake_end_date=datetime.date(2024, 2, 1),
        intake_end_date_precision=P.MONTH,
    ) == "end_date_before_start_date"
    # start "2024" can be on or before an end of 2024-01-05 (mixed precision)
    assert _violated_rule(
        intake_start_date=datetime.date(2024, 1, 1),
        intake_start_date_precision=P.YEAR,
        intake_end_date=datetime.date(2024, 1, 5),
        intake_end_date_precision=P.DAY,
    ) is None
    # same month on both sides
    assert _violated_rule(
        intake_start_date=datetime.date(2024, 3, 1),
        intake_start_date_precision=P.MONTH,
        intake_end_date=datetime.date(2024, 3, 1),
        intake_end_date_precision=P.MONTH,
    ) is None
    assert _violated_rule(
        intake_start_date=datetime.date(2025, 1, 1),
        intake_start_date_precision=P.YEAR,
        intake_end_date=datetime.date(2024, 1, 1),
        intake_end_date_precision=P.YEAR,
    ) == "end_date_before_start_date"


@pytest.mark.parametrize("side", ["start", "end"])
def test_current_month_and_year_are_not_in_the_future(side):
    from medlogserver.model.intake import IntakeDatePrecision as P

    field = f"intake_{side}_date"
    rule = f"{side}_date_in_future"
    # consumed_meds_today stays unset, only the "not in the future" rules apply
    cases = [
        (_UNIT_TODAY.replace(day=1), P.MONTH, None),
        (_first_of_next_month(_UNIT_TODAY), P.MONTH, rule),
        (_UNIT_TODAY.replace(month=1, day=1), P.YEAR, None),
        (datetime.date(_UNIT_TODAY.year + 1, 1, 1), P.YEAR, rule),
    ]
    for value, precision, expected in cases:
        fields = {field: value, f"{field}_precision": precision}
        assert _violated_rule(**fields) == expected, (value, precision)


def test_consumed_today_rules_with_imprecise_dates():
    from medlogserver.model.intake import ConsumedMedsTodayAnswers, IntakeDatePrecision as P

    yes = dict(consumed_meds_today=ConsumedMedsTodayAnswers.YES)
    interview = _reference(today=_UNIT_TODAY, interview_date=_UNIT_TODAY)

    # an end "in this month" may be today
    assert _violated_rule(
        interview,
        **yes,
        intake_end_date=_UNIT_TODAY.replace(day=1),
        intake_end_date_precision=P.MONTH,
    ) is None
    # an end "last month" lies before the interview date
    last_month = (_UNIT_TODAY.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
    assert _violated_rule(
        interview,
        **yes,
        intake_end_date=last_month,
        intake_end_date_precision=P.MONTH,
    ) == "consumed_today_with_past_end_date"

    # a start "this year" may be before the interview, also when the interview
    # was early in the year
    early_interview = _reference(
        today=_UNIT_TODAY, interview_date=_UNIT_TODAY.replace(month=1, day=2)
    )
    assert _violated_rule(
        early_interview,
        **yes,
        intake_start_date=_UNIT_TODAY.replace(month=1, day=1),
        intake_start_date_precision=P.YEAR,
    ) is None
    # a start "this month" cannot have been taken on an interview of last month
    assert _violated_rule(
        _reference(today=_UNIT_TODAY, interview_date=last_month),
        **yes,
        intake_start_date=_UNIT_TODAY.replace(day=1),
        intake_start_date_precision=P.MONTH,
    ) == "consumed_today_with_future_start_date"


@pytest.mark.parametrize("side", ["start", "end"])
def test_implausibly_old_imprecise_dates(side):
    from medlogserver.model.intake import IntakeDatePrecision as P
    from medlogserver.model.intake_rules import EARLIEST_PLAUSIBLE_DATE

    field = f"intake_{side}_date"
    rule = f"{side}_date_implausibly_old"
    floor_year = EARLIEST_PLAUSIBLE_DATE.year
    cases = [
        # the year (month) of the floor reaches the floor
        (datetime.date(floor_year, 1, 1), P.YEAR, None),
        (EARLIEST_PLAUSIBLE_DATE.replace(day=1), P.MONTH, None),
        (datetime.date(floor_year - 1, 1, 1), P.YEAR, rule),
        (EARLIEST_PLAUSIBLE_DATE - datetime.timedelta(days=1), P.DAY, rule),
    ]
    for value, precision, expected in cases:
        fields = {field: value, f"{field}_precision": precision}
        assert _violated_rule(**fields) == expected, (value, precision)


# ── API ────────────────────────────────────────────────────────────────────


def _past_month() -> datetime.date:
    """First day of a month well in the past, so the date rules do not interfere."""
    return (_today() - datetime.timedelta(days=90)).replace(day=1)


def test_post_month_precision_stores_first_day_of_month():
    sent = _past_month().replace(day=15)
    intake = _post(
        _payload(
            intake_start_date=sent.isoformat(), intake_start_date_precision="month"
        )
    )
    assert intake["intake_start_date"] == sent.replace(day=1).isoformat()
    assert intake["intake_start_date_precision"] == "month"
    assert intake["intake_end_date_precision"] is None


def test_post_year_precision_stores_january_first():
    intake = _post(
        _payload(intake_start_date="2020-06-15", intake_start_date_precision="year")
    )
    assert intake["intake_start_date"] == "2020-01-01"
    assert intake["intake_start_date_precision"] == "year"


def test_post_without_precision_is_an_exact_day():
    """Clients that do not know the precision keep working."""
    payload = _payload()
    assert "intake_start_date_precision" not in payload
    intake = _post(payload)
    assert intake["intake_start_date"] == payload["intake_start_date"]
    assert intake["intake_start_date_precision"] == "day"


def test_post_mixed_precision():
    start = _past_month()
    intake = _post(
        _payload(
            intake_start_date=start.isoformat(),
            intake_start_date_precision="year",
            intake_end_date=_today().isoformat(),
            intake_end_date_precision="day",
        )
    )
    assert intake["intake_start_date"] == start.replace(month=1).isoformat()
    assert intake["intake_start_date_precision"] == "year"
    assert intake["intake_end_date"] == _today().isoformat()
    assert intake["intake_end_date_precision"] == "day"


def test_post_precision_with_option_rejected():
    response = _post(
        _payload(intake_start_date_option="unknown", intake_start_date_precision="month"),
        expected_http_code=422,
    )
    assert "must be null" in str(response["detail"])


def test_post_unknown_precision_rejected():
    _post(_payload(intake_start_date_precision="week"), expected_http_code=422)


def test_post_current_month_as_start_accepted_next_month_rejected():
    intake = _post(
        _payload(
            intake_start_date=_today().isoformat(),
            intake_start_date_precision="month",
        )
    )
    assert intake["intake_start_date"] == _today().replace(day=1).isoformat()

    response = _post(
        _payload(
            intake_start_date=_first_of_next_month(_today()).isoformat(),
            intake_start_date_precision="month",
            consumed_meds_today="No",
        ),
        expected_http_code=422,
    )
    _assert_rejected_by(response, "start_date_in_future")


def test_patch_precision_without_date_rejected():
    intake = _post(_payload())
    response = _patch(
        intake["id"], {"intake_start_date_precision": "month"}, expected_http_code=422
    )
    assert "can only be sent together with" in str(response["detail"])


def test_patch_precision_follows_date_and_option():
    start = _past_month()
    intake = _post(
        _payload(
            intake_start_date=start.replace(day=20).isoformat(),
            intake_start_date_precision="month",
        )
    )
    assert intake["intake_start_date"] == start.isoformat()

    # a date without precision is an exact day again
    patched = _patch(intake["id"], {"intake_start_date": start.replace(day=20).isoformat()})
    assert patched["intake_start_date"] == start.replace(day=20).isoformat()
    assert patched["intake_start_date_precision"] == "day"

    # switching to an option clears the precision
    patched = _patch(intake["id"], {"intake_start_date_option": "unknown"})
    assert patched["intake_start_date"] is None
    assert patched["intake_start_date_precision"] is None

    # and back to a year
    patched = _patch(
        intake["id"],
        {"intake_start_date": start.isoformat(), "intake_start_date_precision": "year"},
    )
    assert patched["intake_start_date"] == start.replace(month=1).isoformat()
    assert patched["intake_start_date_precision"] == "year"


def test_patch_end_month_is_checked_against_stored_start_day():
    """The merged record carries the precision, the rule uses the whole month."""
    start = _past_month().replace(day=20)
    intake = _post(_payload(intake_start_date=start.isoformat(), consumed_meds_today="No"))

    patched = _patch(
        intake["id"],
        {"intake_end_date": start.isoformat(), "intake_end_date_precision": "month"},
    )
    assert patched["intake_end_date"] == start.replace(day=1).isoformat()
    assert patched["intake_end_date_precision"] == "month"

    month_before = (start.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
    response = _patch(
        intake["id"],
        {"intake_end_date": month_before.isoformat(), "intake_end_date_precision": "month"},
        expected_http_code=422,
    )
    _assert_rejected_by(response, "end_date_before_start_date")


# ── export ─────────────────────────────────────────────────────────────────


def test_export_columns_of_imprecise_dates():
    from medlogserver.model.intake import Intake, IntakeExport
    from medlogserver.worker.tasks.export_layout import flatten_export_objects

    intake = Intake(
        **_create_model(
            intake_start_date="2024-03-10",
            intake_start_date_precision="month",
            intake_end_date_option="unknown",
        ).model_dump()
    )
    columns = flatten_export_objects(IntakeExport.model_validate(intake), "intake")
    assert {k: v for k, v in columns.items() if k.startswith("intake_start_date")} == {
        "intake_start_date": "2024-03",
        "intake_start_date_option": None,
        "intake_start_date_precision": "month",
        "intake_start_date_earliest": datetime.date(2024, 3, 1),
        "intake_start_date_latest": datetime.date(2024, 3, 31),
    }
    assert {k: v for k, v in columns.items() if k.startswith("intake_end_date")} == {
        "intake_end_date": None,
        "intake_end_date_option": "unknown",
        "intake_end_date_precision": None,
        "intake_end_date_earliest": None,
        "intake_end_date_latest": None,
    }


def test_export_columns_are_in_the_layout():
    columns = _export_layout().csv_columns()
    for side in ("start", "end"):
        date_column = f"intake_{side}_date"
        assert f"{date_column}_precision" in columns
        # earliest and latest follow each other
        earliest = columns.index(f"{date_column}_earliest")
        assert columns[earliest + 1] == f"{date_column}_latest"


def _create_export_study() -> str:
    """A study with one intake per precision, created through the API."""
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestIntakeDatePrecisionExport",
        with_events=1,
        with_interviews_per_event_per_proband=1,
        with_intakes=0,
        proband_count=1,
    )
    study_id = str(study_data.study.id)
    interview_id = study_data.events[0].interviews[0].interview.id
    for overrides in (
        dict(intake_start_date="2024-03-10"),
        dict(intake_start_date="2024-03-10", intake_start_date_precision="month"),
        dict(
            intake_start_date="2024-03-10",
            intake_start_date_precision="year",
            intake_end_date="2025-02-10",
            intake_end_date_precision="month",
        ),
        dict(intake_start_date_option="unknown"),
    ):
        req(
            f"api/study/{study_id}/interview/{interview_id}/intake",
            method="post",
            b=_payload(consumed_meds_today="No", **overrides),
        )
    return study_id


def test_export_of_imprecise_dates_validates_against_schemas(session_db, tmp_path):
    from tests_export_schema import _build_schemas, _json_schema_errors, _validate_csv
    from medlogserver.model.export_schema import ExportSchemaFormat
    from medlogserver.worker.tasks.export_study_data import StudyDataExporter

    study_id = uuid.UUID(_create_export_study())
    schemas = _build_schemas()

    csv_target = tmp_path / "export.csv"
    _run_export(session_db, StudyDataExporter, study_id, "csv", csv_target)
    csv_text = csv_target.read_text(encoding="utf-8")
    report = _validate_csv(schemas[ExportSchemaFormat.CSV], tmp_path, csv_text)
    assert report.valid, report.flatten(["rowNumber", "fieldName", "type", "note"])

    date_columns = [
        f"intake_{side}_date{suffix}"
        for side in ("start", "end")
        for suffix in ("", "_precision", "_earliest", "_latest")
    ]
    rows = sorted(
        (
            tuple(row[c] for c in date_columns)
            for row in csv.DictReader(io.StringIO(csv_text))
        ),
    )
    assert rows == sorted(
        [
            ("2024-03-10", "day", "2024-03-10", "2024-03-10", "", "", "", ""),
            ("2024-03", "month", "2024-03-01", "2024-03-31", "", "", "", ""),
            (
                "2024", "year", "2024-01-01", "2024-12-31",
                "2025-02", "month", "2025-02-01", "2025-02-28",
            ),
            ("", "", "", "", "", "", "", ""),
        ]
    )

    json_target = tmp_path / "export.json"
    _run_export(session_db, StudyDataExporter, study_id, "json", json_target)
    export: Dict[str, Any] = json.loads(json_target.read_text(encoding="utf-8"))
    assert _json_schema_errors(schemas[ExportSchemaFormat.JSON], export) == []
    year_intake = next(
        i["intake"]
        for i in export["intakes"]
        if i["intake"]["intake_start_date_precision"] == "year"
    )
    assert year_intake["intake_start_date"] == "2024"
    assert year_intake["intake_start_date_earliest"] == "2024-01-01"
    assert year_intake["intake_end_date_latest"] == "2025-02-28"


def test_export_schema_documents_the_new_columns():
    from tests_export_schema import _build_schemas
    from medlogserver.model.export_schema import ExportSchemaFormat

    fields = {
        field["name"]: field
        for field in _build_schemas()[ExportSchemaFormat.CSV]["fields"]
    }
    for side in ("start", "end"):
        date_column = f"intake_{side}_date"
        # reduced precision values are no Table Schema dates
        assert fields[date_column]["type"] == "string"
        assert "YYYY-MM" in fields[date_column]["description"]
        assert fields[f"{date_column}_precision"]["constraints"]["enum"] == [
            "day",
            "month",
            "year",
        ]
        for suffix in ("_earliest", "_latest"):
            assert fields[f"{date_column}{suffix}"]["type"] == "date"
            assert fields[f"{date_column}{suffix}"]["description"]


# ── migration ──────────────────────────────────────────────────────────────


def _run_precision_migration(connection):
    import importlib.util
    from pathlib import Path

    from alembic.operations import Operations
    from alembic.runtime.migration import MigrationContext

    mig_path = (
        Path(__file__).resolve().parent.parent
        / "medlogserver/db_migrations/versions/"
        "c5d6e7f8a9b0_add_intake_date_precision.py"
    )
    spec = importlib.util.spec_from_file_location("mig_c5d6e7f8a9b0", mig_path)
    mig = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mig)
    mig.op = Operations(MigrationContext.configure(connection))
    mig.upgrade()


def _migration_test_engine(request, tmp_path):
    """A sync engine on an empty database of the backend the tests run on.

    For Postgres a scratch database next to the test database, so the migration
    runs against a real native ENUM and never touches the tables of the run.
    """
    import os
    import sqlalchemy as sa

    if request.config.getoption("--db") != "postgres":
        return sa.create_engine(f"sqlite:///{tmp_path / 'mig_date_precision.db'}"), None

    url = sa.engine.make_url(os.environ["SQL_DATABASE_URL"]).set(
        drivername="postgresql+psycopg"
    )
    scratch_db = f"mig_date_precision_{uuid.uuid4().hex[:8]}"
    admin = sa.create_engine(url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(sa.text(f'CREATE DATABASE "{scratch_db}"'))

    def drop():
        with admin.connect() as conn:
            conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{scratch_db}"'))
        admin.dispose()

    return sa.create_engine(url.set(database=scratch_db)), drop


def test_migration_backfills_day_precision(request, tmp_path):
    import sqlalchemy as sa

    engine, drop = _migration_test_engine(request, tmp_path)
    try:
        with engine.begin() as conn:
            conn.execute(
                sa.text(
                    "CREATE TABLE intake (id VARCHAR PRIMARY KEY, "
                    "intake_start_date DATE, intake_start_date_option VARCHAR(32), "
                    "intake_end_date DATE, intake_end_date_option VARCHAR(32))"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO intake VALUES "
                    "('both_dates', '2024-03-15', NULL, '2024-04-01', NULL), "
                    "('start_date_end_option', '2024-03-15', NULL, NULL, 'ONGOING'), "
                    "('options_only', NULL, 'UNKNOWN', NULL, 'UNKNOWN')"
                )
            )
        with engine.begin() as conn:
            _run_precision_migration(conn)
        with engine.connect() as conn:
            # SQLite returns the dates as strings, Postgres as dates
            rows = {
                row[0]: tuple(None if v is None else str(v) for v in row[1:])
                for row in conn.execute(
                    sa.text(
                        "SELECT id, intake_start_date, intake_start_date_precision, "
                        "intake_end_date, intake_end_date_precision FROM intake"
                    )
                )
            }
            # the native enum accepts every precision
            conn.execute(
                sa.text(
                    "UPDATE intake SET intake_start_date_precision = 'MONTH', "
                    "intake_end_date_precision = 'YEAR' WHERE id = 'both_dates'"
                )
            )
    finally:
        engine.dispose()
        if drop is not None:
            drop()

    # dates are not touched, existing placeholder days stay
    assert rows == {
        "both_dates": ("2024-03-15", "DAY", "2024-04-01", "DAY"),
        "start_date_end_option": ("2024-03-15", "DAY", None, None),
        "options_only": (None, None, None, None),
    }
