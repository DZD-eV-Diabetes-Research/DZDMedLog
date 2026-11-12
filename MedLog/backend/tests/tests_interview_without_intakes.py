"""Interviews without intakes (issue #404).

* An interview answered with "no meds taken" has no intakes. It must still show up
  in the study export, as a row with empty intake and drug columns (CSV) or an entry
  with `intake` null (JSON), so the export shows that the interview took place.
* If such an interview gets an intake later, its `proband_has_taken_meds` flag must
  switch to true.
"""

import asyncio
import csv
import datetime
import io
import json
import uuid

from sqlmodel.ext.asyncio.session import AsyncSession

from utils import req, dictyfy, create_test_study, TestDataContainerStudy
from tests_export_performance import (
    session_db,
    _export_layout,
    _pick_imported_drug_ids,
    _run_export,
    _seed_study,
)
from tests_export_schema import _build_schemas, _json_schema_errors, _validate_csv

from medlogserver.model.export_schema import ExportSchemaFormat
from medlogserver.model.interview import Interview
from medlogserver.model.intake import IntakeCreateAPI, ConsumedMedsTodayAnswers
from medlogserver.worker.tasks.export_study_data import StudyDataExporter

SEEDED_INTAKES = 10


def _seed_study_with_interviews_without_intakes(session_db, name: str):
    """A seeded study with intakes plus two interviews answered with "no meds"."""
    seeded = _seed_study(
        session_db,
        name=name,
        intake_count=SEEDED_INTAKES,
        drug_ids=_pick_imported_drug_ids(session_db, minimum=3),
    )
    user_id = uuid.UUID(req("api/user/me", method="get")["id"])
    event_id = uuid.UUID(
        req(f"api/study/{seeded.study_id}/event", method="get")["items"][0]["id"]
    )
    interviews = [
        Interview(
            id=uuid.uuid4(),
            event_id=event_id,
            interviewer_user_id=user_id,
            proband_external_id=f"NOMEDS{index}",
            proband_has_taken_meds=False,
            interview_start_time_utc=datetime.datetime(2025, 2, 1, 8, index),
            interview_end_time_utc=datetime.datetime(2025, 2, 1, 9, index),
        )
        for index in range(2)
    ]
    interview_ids = {str(i.id) for i in interviews}

    async def insert():
        async with AsyncSession(session_db.engine) as session:
            session.add_all(interviews)
            await session.commit()

    asyncio.run(insert())
    return seeded.study_id, interview_ids


def test_csv_export_has_a_row_per_interview_without_intakes(session_db, tmp_path):
    study_id, no_meds_ids = _seed_study_with_interviews_without_intakes(
        session_db, "Export interviews without intakes csv"
    )
    target = tmp_path / "export.csv"
    _run_export(session_db, StudyDataExporter, study_id, "csv", target)
    csv_text = target.read_text(encoding="utf-8")
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    assert len(rows) == SEEDED_INTAKES + 2

    # intake rows first, then the interviews without intakes
    no_meds_rows = rows[SEEDED_INTAKES:]
    assert {row["interview_id"] for row in no_meds_rows} == no_meds_ids
    layout = _export_layout()
    intake_and_drug_columns = [
        c for c in layout.csv_columns() if c.startswith(("intake_", "drug_"))
    ]
    assert intake_and_drug_columns
    for row in no_meds_rows:
        assert row["study_id"] == str(study_id)
        assert row["event_id"]
        assert row["interview_proband_has_taken_meds"] == "False"
        assert row["interview_proband_external_id"].startswith("NOMEDS")
        assert {c: row[c] for c in intake_and_drug_columns} == dict.fromkeys(
            intake_and_drug_columns, ""
        )
    for row in rows[:SEEDED_INTAKES]:
        assert row["intake_id"]

    table_schema = _build_schemas()[ExportSchemaFormat.CSV]
    report = _validate_csv(table_schema, tmp_path, csv_text)
    assert report.valid, report.flatten(["rowNumber", "fieldName", "type", "note"])


def test_json_export_has_an_entry_per_interview_without_intakes(session_db, tmp_path):
    study_id, no_meds_ids = _seed_study_with_interviews_without_intakes(
        session_db, "Export interviews without intakes json"
    )
    target = tmp_path / "export.json"
    _run_export(session_db, StudyDataExporter, study_id, "json", target)
    export = json.loads(target.read_text(encoding="utf-8"))
    entries = export["intakes"]
    assert len(entries) == SEEDED_INTAKES + 2

    no_meds_entries = entries[SEEDED_INTAKES:]
    assert {e["interview"]["id"] for e in no_meds_entries} == no_meds_ids
    for entry in no_meds_entries:
        assert entry["intake"] is None
        assert entry["drug_codes"] == []
        assert entry["drug_attrs"] == []
        assert entry["interview"]["proband_has_taken_meds"] is False
        assert entry["event"]["id"]
    for entry in entries[:SEEDED_INTAKES]:
        assert entry["intake"]["id"]

    schema = _build_schemas()[ExportSchemaFormat.JSON]
    assert _json_schema_errors(schema, export) == []


def test_export_of_study_with_only_interviews_without_intakes(session_db, tmp_path):
    study = req(
        "api/study", method="post", b={"display_name": "Export only no-meds interviews"}
    )
    study_id = study["id"]
    event = req(f"api/study/{study_id}/event", method="post", b={"name": "E1"})
    req(
        f"api/study/{study_id}/event/{event['id']}/interview",
        method="post",
        b={"proband_external_id": "ONLYNOMEDS", "proband_has_taken_meds": False},
    )
    target = tmp_path / "export.csv"
    _run_export(session_db, StudyDataExporter, uuid.UUID(study_id), "csv", target)
    rows = list(csv.DictReader(io.StringIO(target.read_text(encoding="utf-8"))))
    assert len(rows) == 1
    assert rows[0]["interview_proband_external_id"] == "ONLYNOMEDS"
    assert rows[0]["intake_id"] == ""


def test_adding_an_intake_switches_proband_has_taken_meds():
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestInterviewNoMedsGetsIntake",
        with_events=1,
        proband_count=1,
    )
    study_id = str(study_data.study.id)
    event_id = str(study_data.events[0].event.id)
    interview = req(
        f"api/study/{study_id}/event/{event_id}/interview",
        method="post",
        b={"proband_external_id": "NOMEDSLATER", "proband_has_taken_meds": False},
    )
    interview_path = f"api/study/{study_id}/event/{event_id}/interview/{interview['id']}"
    assert req(interview_path, method="get")["proband_has_taken_meds"] is False

    drug = req("/api/drug/search", method="get", q={"search_term": "Test2Drug"})[
        "items"
    ][0]["drug"]
    req(
        f"api/study/{study_id}/interview/{interview['id']}/intake",
        method="post",
        b=dictyfy(
            IntakeCreateAPI(
                drug_id=drug["id"],
                intake_start_date=datetime.date(2024, 1, 1),
                consumed_meds_today=ConsumedMedsTodayAnswers.NO,
                as_needed_dose_unit=None,
            )
        ),
    )
    assert req(interview_path, method="get")["proband_has_taken_meds"] is True
