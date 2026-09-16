"""Regression tests and benchmark for the study export performance (issue #362).

The export used to load every intake's drug with its own session and about nine
queries, so the query count grew with the number of intake rows (1000 rows took
4 to 5 minutes on production). These tests make sure that

* the rewritten exporter produces byte-identical CSV and JSON files compared to
  the exporter before #362 (frozen in `export_reference_pre_issue_362.py`),
* the number of queries depends on the number of distinct drugs, not on the
  number of intake rows.

The studies are seeded directly into the session database instead of via the
REST API, because creating thousands of intakes one request at a time would take
longer than the export itself. The exporters run in the test process against the
same database.

Benchmark
---------
`test_export_benchmark` is skipped unless `MEDLOG_EXPORT_BENCHMARK_ROWS` is set to a
comma separated list of intake row counts. It prints duration, query count and peak
Python memory for the old and the new exporter::

    MEDLOG_EXPORT_BENCHMARK_ROWS=1000,10000 \\
        ./run_backend_tests_with_sqlite.sh -k test_export_benchmark -s

The old exporter is only run up to `MEDLOG_EXPORT_BENCHMARK_LEGACY_MAX_ROWS` rows
(default 2000) because it gets very slow. The dummy drug dataset only has a few
dozen drugs, so `MEDLOG_EXPORT_BENCHMARK_CUSTOM_DRUGS` (default 300) custom drugs are
added to get a realistic number of distinct drugs. Use
`run_backend_tests_with_postgres.sh` with the same arguments to benchmark PostgreSQL.

For the old JSON export the numbers come from `LegacyJsonReferenceExporter`, because
the real one crashed (see there).
"""

from typing import Any, Dict, List, Literal, Tuple
import asyncio
import datetime
import json
import os
import random
import time
import tracemalloc
import uuid
from dataclasses import dataclass
from pathlib import Path

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from pydantic_core import to_json

from utils import req, dictyfy
from export_reference_pre_issue_362 import (
    ExportContainer as LegacyExportContainer,
    LegacyStudyDataExporter,
    ValueReferenceCodeNotApplicable as LegacyValueReferenceCodeNotApplicable,
)

from medlogserver.model.drug_data.drug import DrugData, DrugCustomCreate
from medlogserver.model.drug_data.drug_attr import DrugMultiValApiCreate
from medlogserver.model.event import Event
from medlogserver.model.interview import Interview
from medlogserver.model.intake import (
    Intake,
    AdministeredByDoctorAnswers,
    ConsumedMedsTodayAnswers,
    IntakeRegularOrAsNeededAnswers,
    IntervalOfDailyDoseAnswers,
    SourceOfDrugInformationAnwers,
)
from medlogserver.worker.tasks.export_study_data import StudyDataExporter

ExportFormat = Literal["csv", "json"]


@dataclass
class SeededStudy:
    study_id: uuid.UUID
    intake_count: int
    distinct_drug_count: int


@dataclass
class ExportTestDB:
    engine: AsyncEngine
    # number of executed SQL statements, reset by `_run_export()`
    statement_count: int = 0


@pytest.fixture
def session_db(monkeypatch):
    """Wire the db layer to a NullPool engine on the session database.

    Every test drives its own `asyncio.run()`, so pooled connections must not
    outlive the loop that opened them. Executed statements are counted in
    `ExportTestDB.statement_count`.
    """
    engine = create_async_engine(
        os.environ["SQL_DATABASE_URL"], future=True, poolclass=NullPool
    )
    db = ExportTestDB(engine=engine)

    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def _count(conn, cursor, statement, parameters, context, executemany):
        db.statement_count += 1

    from medlogserver.db import _session

    monkeypatch.setattr(_session, "_db_engine", engine)
    monkeypatch.setattr(
        _session,
        "_async_session_factory",
        sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
        ),
    )
    monkeypatch.setattr(_session, "_engine_pid", os.getpid())

    yield db

    asyncio.run(engine.dispose())


def _create_custom_drug_with_multi_ref(trade_name: str) -> uuid.UUID:
    """A drug with multi reference values, the most complex export column type."""
    drug = req(
        "api/drug/custom",
        method="post",
        b=dictyfy(
            DrugCustomCreate(
                trade_name=trade_name,
                custom_drug_notes="Notes with, a comma and a\nline break",
                attrs_multi_ref=[
                    DrugMultiValApiCreate(
                        field_name="producing_country", values=["DE", "UK"]
                    )
                ],
            )
        ),
    )
    return uuid.UUID(drug["id"])


def _seed_study(
    db: ExportTestDB,
    name: str,
    intake_count: int,
    drug_ids: List[uuid.UUID],
    event_count: int = 3,
    intakes_per_interview: int = 5,
    seed: int = 362,
) -> SeededStudy:
    """Create a study via API and insert events, interviews and intakes directly."""
    study = req("api/study", method="post", b={"display_name": name})
    user_id = uuid.UUID(req("api/user/me", method="get")["id"])
    rnd = random.Random(seed)
    study_id = uuid.UUID(study["id"])

    events = [
        Event(
            id=uuid.uuid4(), study_id=study_id, name=f"Event{i}", order_position=i
        )
        for i in range(event_count)
    ]
    interviews: List[Interview] = []
    intakes: List[Intake] = []
    start = datetime.datetime(2025, 1, 1, 8, 0, 0)
    for index in range(intake_count):
        if index % intakes_per_interview == 0:
            interviews.append(
                Interview(
                    id=uuid.uuid4(),
                    event_id=events[len(interviews) % event_count].id,
                    interviewer_user_id=user_id,
                    proband_external_id=f"P{len(interviews):06d}",
                    proband_has_taken_meds=True,
                    interview_start_time_utc=start
                    + datetime.timedelta(minutes=len(interviews)),
                )
            )
        regular = rnd.random() < 0.5
        intakes.append(
            Intake(
                id=uuid.uuid4(),
                interview_id=interviews[-1].id,
                drug_id=rnd.choice(drug_ids),
                source_of_drug_information=rnd.choice(
                    list(SourceOfDrugInformationAnwers)
                ),
                intake_start_date=datetime.date(2024, 1, 1)
                + datetime.timedelta(days=rnd.randint(0, 300)),
                administered_by_doctor=rnd.choice(list(AdministeredByDoctorAnswers)),
                intake_regular_or_as_needed=(
                    IntakeRegularOrAsNeededAnswers.REGULAR
                    if regular
                    else IntakeRegularOrAsNeededAnswers.ASNEEDED
                ),
                dose_per_day=rnd.choice([0.5, 1, 2.25]) if regular else None,
                regular_intervall_of_daily_dose=(
                    IntervalOfDailyDoseAnswers.DAILY if regular else None
                ),
                as_needed_dose_unit=None if regular else rnd.randint(1, 4),
                consumed_meds_today=rnd.choice(list(ConsumedMedsTodayAnswers)),
            )
        )

    async def insert():
        async with AsyncSession(db.engine, expire_on_commit=False) as session:
            session.add_all(events)
            await session.flush()
            session.add_all(interviews)
            await session.flush()
            session.add_all(intakes)
            await session.commit()

    asyncio.run(insert())
    return SeededStudy(
        study_id=study_id,
        intake_count=intake_count,
        distinct_drug_count=len({i.drug_id for i in intakes}),
    )


def _pick_imported_drug_ids(db: ExportTestDB, minimum: int) -> List[uuid.UUID]:
    """All drugs of the imported (dummy) drug dataset, which has a few dozen."""

    async def pick():
        async with AsyncSession(db.engine) as session:
            result = await session.exec(
                select(DrugData.id)
                .where(col(DrugData.is_custom_drug).is_(False))
                .order_by(col(DrugData.trade_name))
            )
            return list(result.all())

    drug_ids = asyncio.run(pick())
    assert len(drug_ids) >= minimum, (
        f"Test needs {minimum} imported drugs, database has only {len(drug_ids)}"
    )
    return drug_ids


class LegacyJsonReferenceExporter(LegacyStudyDataExporter):
    """The pre-#362 exporter with the JSON serialization bug worked around.

    Before #362 `model_dump_json()` failed on the `ValueReferenceCodeNotApplicable`
    marker class for every study with intakes, so there is no old JSON output to
    compare with. This builds what the old exporter was meant to write: the same
    gathered data and the same pretty printing, with the not applicable reference
    codes left out (as the fixed exporter and the CSV export do).
    """

    async def export_data_and_write_to_file(self) -> Path:
        exportdata: LegacyExportContainer = await self._gather_export_data()

        def strip_marker(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {
                    k: strip_marker(v)
                    for k, v in obj.items()
                    if v is not LegacyValueReferenceCodeNotApplicable
                }
            if isinstance(obj, list):
                return [strip_marker(v) for v in obj]
            return obj

        Path(self.target_file.parent).mkdir(parents=True, exist_ok=True)
        with open(self.target_file, "w", encoding="utf-8") as target_file:
            target_file.write(
                to_json(strip_marker(exportdata.model_dump()), indent=4).decode()
            )
        return self.target_file


def _run_export(
    db: ExportTestDB,
    exporter_class: type,
    study_id: uuid.UUID,
    format_: ExportFormat,
    target_file: Path,
    trace_memory: bool = False,
) -> Dict[str, float]:
    """Run one export and return duration, statement count and peak memory."""
    db.statement_count = 0
    if trace_memory:
        tracemalloc.start()
    start = time.monotonic()
    result = asyncio.run(
        exporter_class(
            study_id=study_id, format_=format_, target_file=target_file
        ).run()
    )
    duration = time.monotonic() - start
    peak_mb = None
    if trace_memory:
        peak_mb = tracemalloc.get_traced_memory()[1] / 1024 / 1024
        tracemalloc.stop()
    assert result == str(target_file)
    return {
        "duration": duration,
        "statements": db.statement_count,
        "peak_mb": peak_mb,
    }


def _legacy_exporter_class(format_: ExportFormat) -> type:
    return LegacyJsonReferenceExporter if format_ == "json" else LegacyStudyDataExporter


@pytest.mark.parametrize("format_", ["csv", "json"])
def test_export_output_identical_to_pre_issue_362_exporter(
    session_db, tmp_path, format_: ExportFormat
):
    drug_ids = _pick_imported_drug_ids(session_db, minimum=10)
    # custom drug names must be unique (issue #37), so every test uses its own name
    drug_ids.append(
        _create_custom_drug_with_multi_ref(
            f"Export performance test drug with refs {format_}"
        )
    )
    study = _seed_study(
        session_db,
        name=f"Export identical output issue 362 {format_}",
        intake_count=300,
        drug_ids=drug_ids,
    )
    empty_study = _seed_study(
        session_db,
        name=f"Export identical output issue 362 {format_} no intakes",
        intake_count=0,
        drug_ids=drug_ids,
    )
    for seeded in (study, empty_study):
        old_file = tmp_path / f"old_{seeded.study_id}.{format_}"
        new_file = tmp_path / f"new_{seeded.study_id}.{format_}"
        _run_export(
            session_db,
            _legacy_exporter_class(format_),
            seeded.study_id,
            format_,
            old_file,
        )
        _run_export(session_db, StudyDataExporter, seeded.study_id, format_, new_file)
        old_text = old_file.read_text(encoding="utf-8")
        new_text = new_file.read_text(encoding="utf-8")
        if seeded.intake_count:
            # guard against comparing two empty or trivial files
            assert seeded.distinct_drug_count == len(drug_ids)
            assert "producing_country" in old_text
            assert f"Export performance test drug with refs {format_}" in old_text
        assert new_text == old_text, (
            f"{format_} export of study with {seeded.intake_count} intakes differs "
            f"from the pre-#362 exporter. Compare {old_file} and {new_file}"
        )


def test_json_export_is_valid_json_with_reference_codes_only_on_ref_attrs(
    session_db, tmp_path
):
    """Before #362 the JSON export failed for every study that had intakes."""
    drug_id = _create_custom_drug_with_multi_ref(
        "Export performance test drug with refs valid json"
    )
    seeded = _seed_study(
        session_db, name="Export JSON issue 362", intake_count=2, drug_ids=[drug_id]
    )
    target = tmp_path / "export.json"
    _run_export(session_db, StudyDataExporter, seeded.study_id, "json", target)
    export = json.loads(target.read_text(encoding="utf-8"))
    assert export["study"]["display_name"] == "Export JSON issue 362"
    assert len(export["intakes"]) == 2
    attrs = {a["drug_attr_name"]: a for a in export["intakes"][0]["drug_attrs"]}
    assert attrs["trade_name"] == {
        "drug_attr_name": "trade_name",
        "drug_attr_value": "Export performance test drug with refs valid json",
    }
    assert attrs["producing_country"]["drug_attr_value"] == ["Germany", "United Kingdom"]
    assert attrs["producing_country"]["drug_attr_reference_code"] == ["DE", "UK"]


def test_export_query_count_does_not_depend_on_intake_rows(session_db, tmp_path):
    drug_ids = _pick_imported_drug_ids(session_db, minimum=10)[:10]
    small = _seed_study(
        session_db,
        name="Export query count issue 362 small",
        intake_count=100,
        drug_ids=drug_ids,
    )
    large = _seed_study(
        session_db,
        name="Export query count issue 362 large",
        intake_count=800,
        drug_ids=drug_ids,
    )
    assert small.distinct_drug_count == large.distinct_drug_count == len(drug_ids)
    for format_ in ("csv", "json"):
        small_stats = _run_export(
            session_db,
            StudyDataExporter,
            small.study_id,
            format_,
            tmp_path / f"small.{format_}",
        )
        large_stats = _run_export(
            session_db,
            StudyDataExporter,
            large.study_id,
            format_,
            tmp_path / f"large.{format_}",
        )
        assert small_stats["statements"] == large_stats["statements"], (
            f"{format_}: {small_stats['statements']} queries for 100 intakes but "
            f"{large_stats['statements']} for 800 intakes with the same drugs"
        )
        # study, events, interviews, intakes plus one drug batch with its relations
        assert large_stats["statements"] < 20, large_stats


@pytest.mark.skipif(
    not os.getenv("MEDLOG_EXPORT_BENCHMARK_ROWS"),
    reason="Benchmark, set MEDLOG_EXPORT_BENCHMARK_ROWS=1000,10000 to run it",
)
def test_export_benchmark(session_db, tmp_path):
    row_counts = [
        int(r) for r in os.environ["MEDLOG_EXPORT_BENCHMARK_ROWS"].split(",") if r
    ]
    legacy_max_rows = int(os.getenv("MEDLOG_EXPORT_BENCHMARK_LEGACY_MAX_ROWS", "2000"))
    custom_drug_count = int(os.getenv("MEDLOG_EXPORT_BENCHMARK_CUSTOM_DRUGS", "300"))
    # The dummy drug dataset is small. Custom drugs top it up to a realistic number
    # of distinct drugs, many probands still share the same drugs.
    drug_ids = _pick_imported_drug_ids(session_db, minimum=1) + [
        _create_custom_drug_with_multi_ref(f"Export benchmark drug {i}")
        for i in range(custom_drug_count)
    ]

    results: List[Tuple[int, int, str, str, Dict[str, float]]] = []
    for rows in row_counts:
        seeded = _seed_study(
            session_db,
            name=f"Export benchmark issue 362 {rows} rows",
            intake_count=rows,
            drug_ids=drug_ids,
        )
        for format_ in ("csv", "json"):
            exporters: List[Tuple[str, type]] = [("new", StudyDataExporter)]
            if rows <= legacy_max_rows:
                exporters.insert(0, ("old", _legacy_exporter_class(format_)))
            for label, exporter_class in exporters:
                target = tmp_path / f"{label}_{rows}.{format_}"
                stats = _run_export(
                    session_db, exporter_class, seeded.study_id, format_, target
                )
                # separate run, tracemalloc slows everything down considerably
                stats["peak_mb"] = _run_export(
                    session_db,
                    exporter_class,
                    seeded.study_id,
                    format_,
                    target,
                    trace_memory=True,
                )["peak_mb"]
                results.append(
                    (rows, seeded.distinct_drug_count, format_, label, stats)
                )

    lines = [
        f"Export benchmark ({os.environ['SQL_DATABASE_URL'].split(':')[0]})",
        f"{'rows':>6} {'drugs':>6} {'format':>6} {'impl':>4} {'seconds':>9} "
        f"{'queries':>8} {'peak MB':>8}",
    ]
    for rows, drugs, format_, label, stats in results:
        lines.append(
            f"{rows:>6} {drugs:>6} {format_:>6} {label:>4} {stats['duration']:>9.2f} "
            f"{stats['statements']:>8} {stats['peak_mb']:>8.1f}"
        )
    print("\n" + "\n".join(lines))
