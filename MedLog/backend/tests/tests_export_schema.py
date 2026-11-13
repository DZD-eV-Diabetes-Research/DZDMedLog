"""Schemas of the study export (issue #387, part 2).

* Exports of a test study validate against the built JSON Schema / Table Schema.
* The schemas are built by a worker job after a successful drug data load and on
  startup when none exists for the running version, and are served by the API.
"""

from types import SimpleNamespace
import asyncio
import copy
import csv
import io
import json
import time
import uuid

import jsonschema
import frictionless
import pytest
from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from utils import req
from tests_export_performance import (
    session_db,
    _create_custom_drug_with_multi_ref,
    _export_layout,
    _pick_imported_drug_ids,
    _run_export,
    _seed_study,
)
from tests_export_stable_columns import _create_custom_drug_with_trade_name_only

from medlogserver.model.export_schema import ExportSchema, ExportSchemaFormat
from medlogserver.model.worker_job import WorkerJob, WorkerJobState
from medlogserver.worker.tasks import Tasks
from medlogserver.worker.tasks import export_schema_build
from medlogserver.worker.tasks import drug_data_load
from medlogserver.worker.tasks.export_schema import (
    ExportSchemaVersions,
    build_export_schemas,
)
from medlogserver.worker.tasks.export_study_data import StudyDataExporter
from medlogserver.db.worker_job import WorkerJobCRUD

TEST_VERSIONS = ExportSchemaVersions(
    medlog_version="0.0.0-test",
    drug_importer="DummyDrugImporterV1",
    drug_dataset_name="DummyDrugs",
    drug_dataset_version="test",
)


def _build_schemas(layout=None):
    layout = layout or _export_layout()
    reference_values = asyncio.run(export_schema_build.load_reference_values(layout))
    return build_export_schemas(layout, reference_values, TEST_VERSIONS)


def _seed_export_study(session_db, name: str) -> uuid.UUID:
    imported_drug_ids = _pick_imported_drug_ids(session_db, minimum=10)
    return _seed_study(
        session_db,
        name=name,
        intake_count=40,
        drug_ids=imported_drug_ids
        + [
            _create_custom_drug_with_trade_name_only(f"{name} drug without attrs"),
            _create_custom_drug_with_multi_ref(f"{name} drug with refs"),
        ],
    ).study_id


def _json_schema_errors(schema, document):
    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )
    return list(validator.iter_errors(document))


def _validate_csv(table_schema, tmp_path, csv_text: str) -> frictionless.Report:
    (tmp_path / "validate.csv").write_text(csv_text, encoding="utf-8")
    return frictionless.validate(
        frictionless.Resource(
            path="validate.csv",
            basepath=str(tmp_path),
            schema=frictionless.Schema.from_descriptor(table_schema),
        )
    )


def _drug_attr(intake, name):
    return next(a for a in intake["drug_attrs"] if a["drug_attr_name"] == name)


#########################
# Schema content        #
#########################


def test_json_export_validates_against_json_schema(session_db, tmp_path):
    study_id = _seed_export_study(session_db, "Export schema json")
    schema = _build_schemas()[ExportSchemaFormat.JSON]
    jsonschema.Draft202012Validator.check_schema(schema)
    target = tmp_path / "export.json"
    _run_export(session_db, StudyDataExporter, study_id, "json", target)
    export = json.loads(target.read_text(encoding="utf-8"))
    assert len(export["intakes"]) == 40
    assert _json_schema_errors(schema, export) == []
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["medlog_version"] == TEST_VERSIONS.medlog_version
    assert schema["drug_dataset_version"] == TEST_VERSIONS.drug_dataset_version


def test_json_schema_rejects_unknown_attrs_and_reference_values(session_db, tmp_path):
    study_id = _seed_export_study(session_db, "Export schema json invalid")
    schema = _build_schemas()[ExportSchemaFormat.JSON]
    target = tmp_path / "export.json"
    _run_export(session_db, StudyDataExporter, study_id, "json", target)
    export = json.loads(target.read_text(encoding="utf-8"))

    unknown_attr = copy.deepcopy(export)
    unknown_attr["intakes"][0]["drug_attrs"].append(
        {"drug_attr_name": "not_an_attr", "drug_attr_value": "x"}
    )
    assert _json_schema_errors(schema, unknown_attr)

    unknown_code = copy.deepcopy(export)
    _drug_attr(unknown_code["intakes"][0], "dispensingtype")[
        "drug_attr_reference_code"
    ] = "not-a-code"
    assert _json_schema_errors(schema, unknown_code)

    # a multi attribute must be a list, not a single value
    single_multi_value = copy.deepcopy(export)
    _drug_attr(single_multi_value["intakes"][0], "keywords")["drug_attr_value"] = "x"
    assert _json_schema_errors(schema, single_multi_value)

    # attributes that are no reference have no reference code
    code_on_plain_attr = copy.deepcopy(export)
    _drug_attr(code_on_plain_attr["intakes"][0], "manufacturer")[
        "drug_attr_reference_code"
    ] = None
    assert _json_schema_errors(schema, code_on_plain_attr)


def test_csv_export_validates_against_table_schema(session_db, tmp_path):
    study_id = _seed_export_study(session_db, "Export schema csv")
    table_schema = _build_schemas()[ExportSchemaFormat.CSV]
    assert list(frictionless.Schema.metadata_validate(table_schema)) == []
    target = tmp_path / "export.csv"
    _run_export(session_db, StudyDataExporter, study_id, "csv", target)
    csv_text = target.read_text(encoding="utf-8")

    header = csv.DictReader(io.StringIO(csv_text)).fieldnames
    assert header == [field["name"] for field in table_schema["fields"]]
    assert header == _export_layout().csv_columns()
    report = _validate_csv(table_schema, tmp_path, csv_text)
    assert report.valid, report.flatten(["rowNumber", "fieldName", "type", "note"])

    # an unknown reference code is reported
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)
    rows[0]["drug_attr_reference_code_dispensingtype"] = "not-a-code"
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=reader.fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    report = _validate_csv(table_schema, tmp_path, out.getvalue())
    assert not report.valid
    assert {
        (error[0], error[1])
        for error in report.flatten(["fieldName", "type"])
    } == {("drug_attr_reference_code_dispensingtype", "constraint-error")}


def test_enum_only_for_small_reference_lists():
    layout = _export_layout()
    schemas = _build_schemas(layout)
    fields = {f["name"]: f for f in schemas[ExportSchemaFormat.CSV]["fields"]}
    assert fields["drug_attr_reference_code_dispensingtype"]["constraints"]["enum"]

    dispensingtype = layout.drug_attrs_by_name["dispensingtype"]
    dispensingtype.field_definition = dispensingtype.field_definition.model_copy(
        update={"is_large_reference_list": True}
    )
    schemas = _build_schemas(layout)
    fields = {f["name"]: f for f in schemas[ExportSchemaFormat.CSV]["fields"]}
    assert "constraints" not in fields["drug_attr_reference_code_dispensingtype"]
    rule = next(
        rule
        for rule in schemas[ExportSchemaFormat.JSON]["$defs"]["DrugDataExport"]["allOf"]
        if rule["if"]["properties"]["drug_attr_name"]["const"] == "dispensingtype"
    )
    assert "enum" not in rule["then"]["properties"]["drug_attr_reference_code"]


#########################
# Worker job            #
#########################


def _record_calls(monkeypatch, target, name: str) -> list:
    calls = []

    async def record(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(target, name, record)
    return calls


@pytest.mark.parametrize("dataset_imported", [True, False])
def test_drug_load_queues_schema_build_only_after_an_import(
    monkeypatch, dataset_imported
):
    async def load(self):
        return dataset_imported

    monkeypatch.setattr(
        drug_data_load.DrugDataLoader, "load_new_drug_data_if_available", load
    )
    cleaning = _record_calls(
        monkeypatch, drug_data_load.DrugDataLoader, "create_follow_up_job_drug_data_cleaning"
    )
    schema_build = _record_calls(
        monkeypatch, drug_data_load.DrugDataLoader, "create_follow_up_job_export_schema_build"
    )
    job = SimpleNamespace(id=uuid.uuid4(), user_id=None)
    asyncio.run(drug_data_load.TaskDrugDataLoading(job=job).work())
    assert len(cleaning) == 1
    assert len(schema_build) == (1 if dataset_imported else 0)


def test_drug_load_failure_queues_no_schema_build(monkeypatch):
    async def load(self):
        raise ValueError("import failed")

    monkeypatch.setattr(
        drug_data_load.DrugDataLoader, "load_new_drug_data_if_available", load
    )
    schema_build = _record_calls(
        monkeypatch, drug_data_load.DrugDataLoader, "create_follow_up_job_export_schema_build"
    )
    job = SimpleNamespace(id=uuid.uuid4(), user_id=None)
    with pytest.raises(ValueError):
        asyncio.run(drug_data_load.TaskDrugDataLoading(job=job).work())
    assert schema_build == []


def test_follow_up_schema_build_job_is_created_with_tags(session_db):
    loader = drug_data_load.DrugDataLoader()
    loader.importer.version = "20990101"
    parent_job_id = uuid.uuid4()
    asyncio.run(loader.create_follow_up_job_export_schema_build(None, parent_job_id))

    async def find_job():
        async with AsyncSession(session_db.engine) as session:
            jobs = (
                await session.exec(
                    select(WorkerJob).where(
                        WorkerJob.task_name == Tasks.EXPORT_SCHEMA_BUILD.name
                    )
                )
            ).all()
        return [j for j in jobs if f"triggeredByJobID:{parent_job_id}" in j.tags]

    jobs = asyncio.run(find_job())
    assert len(jobs) == 1
    assert {"drug-loading", "export-schema", "version:20990101"} <= set(jobs[0].tags)


def test_startup_queues_schema_build_when_missing(session_db, monkeypatch):
    monkeypatch.setattr(
        export_schema_build, "medlog_version", lambda: f"test-{uuid.uuid4()}"
    )
    created = _record_calls(
        monkeypatch, export_schema_build, "create_export_schema_build_job"
    )

    # Other tests (and the drug load on server start) queue real build jobs
    async def no_pending_jobs(self, **kwargs):
        return []

    monkeypatch.setattr(WorkerJobCRUD, "list", no_pending_jobs)
    asyncio.run(export_schema_build.queue_export_schema_build_if_missing())
    assert len(created) == 1
    assert created[0][1]["tags"] == ["init-job"]


def test_startup_queues_no_schema_build_when_one_is_pending(session_db, monkeypatch):
    monkeypatch.setattr(
        export_schema_build, "medlog_version", lambda: f"test-{uuid.uuid4()}"
    )
    created = _record_calls(
        monkeypatch, export_schema_build, "create_export_schema_build_job"
    )

    async def pending_job(self, **kwargs):
        assert kwargs["filter_task"] == Tasks.EXPORT_SCHEMA_BUILD
        return [SimpleNamespace(get_state=lambda: WorkerJobState.QUEUED)]

    monkeypatch.setattr(WorkerJobCRUD, "list", pending_job)
    asyncio.run(export_schema_build.queue_export_schema_build_if_missing())
    assert created == []


def test_startup_queues_no_schema_build_when_schemas_exist(session_db, monkeypatch):
    version = f"test-{uuid.uuid4()}"
    monkeypatch.setattr(export_schema_build, "medlog_version", lambda: version)
    created = _record_calls(
        monkeypatch, export_schema_build, "create_export_schema_build_job"
    )
    drug_dataset = asyncio.run(export_schema_build.get_active_drug_dataset())

    async def store(rows):
        async with AsyncSession(session_db.engine) as session:
            for row in rows:
                session.add(row)
            await session.commit()

    async def remove():
        async with AsyncSession(session_db.engine) as session:
            await session.exec(
                delete(ExportSchema).where(ExportSchema.medlog_version == version)
            )
            await session.commit()

    asyncio.run(
        store(
            [
                ExportSchema(
                    medlog_version=version,
                    drug_dataset_version=drug_dataset.dataset_version,
                    format=format_.value,
                    content={},
                )
                for format_ in ExportSchemaFormat
            ]
        )
    )
    try:
        asyncio.run(export_schema_build.queue_export_schema_build_if_missing())
    finally:
        asyncio.run(remove())
    assert created == []


def test_startup_queues_no_schema_build_without_active_drug_dataset(monkeypatch):
    async def no_dataset():
        return None

    monkeypatch.setattr(export_schema_build, "get_active_drug_dataset", no_dataset)
    created = _record_calls(
        monkeypatch, export_schema_build, "create_export_schema_build_job"
    )
    asyncio.run(export_schema_build.queue_export_schema_build_if_missing())
    assert created == []


#########################
# API                   #
#########################


def _wait_for_export_schema(export_format: str, timeout_sec: int = 120):
    """The schema is built by the background worker, poll until it is there."""
    deadline = time.monotonic() + timeout_sec
    while True:
        response = req(
            f"api/export/schema/{export_format}", tolerated_error_codes=[503]
        )
        if isinstance(response, dict) and "detail" not in response:
            return response
        assert time.monotonic() < deadline, (
            f"Export schema '{export_format}' was not built within {timeout_sec}s: "
            f"{response}"
        )
        time.sleep(2)


def test_export_schema_endpoints():
    json_schema = _wait_for_export_schema("json")
    assert json_schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    jsonschema.Draft202012Validator.check_schema(json_schema)
    table_schema = _wait_for_export_schema("csv")
    assert [f["name"] for f in table_schema["fields"]] == (
        _export_layout().csv_columns()
    )
    # both schemas were built for the same versions
    for key in ("medlog_version", "drug_dataset_name", "drug_dataset_version"):
        assert json_schema[key] == table_schema[key]
    req("api/export/schema/xml", expected_http_code=422)


def test_export_schema_requires_authentication():
    req("api/export/schema/json", suppress_auth=True, expected_http_code=401)


def test_export_schema_not_built_yet_returns_503(session_db):
    _wait_for_export_schema("json")

    async def remove_all():
        async with AsyncSession(session_db.engine) as session:
            await session.exec(delete(ExportSchema))
            await session.commit()

    asyncio.run(remove_all())
    response = req("api/export/schema/json", expected_http_code=503)
    assert "not built yet" in response["detail"]

    # a new build job restores it
    asyncio.run(export_schema_build.create_export_schema_build_job())
    _wait_for_export_schema("json")
    _wait_for_export_schema("csv")
