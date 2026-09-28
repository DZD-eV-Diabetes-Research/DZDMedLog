"""Regression tests for the obsolete drug data cleanup (issue #331).

`tests_drug_db_updater.py` already covers the cleanup end to end, but only checks
that the obsolete `drug` row itself disappears. It never looks at the child rows.
That is exactly how the SQLite orphan bug stayed unnoticed: `PRAGMA foreign_keys`
is off there, so the ON DELETE CASCADE silently did nothing, the drug rows still
vanished, and the end-to-end test stayed green while `drug_attr_val`, `drug_code`
and the search cache kept filling up with orphans.

These tests therefore assert on the child tables, and run the whole thing twice:

- `foreign_keys=OFF`  mirrors how SQLite deployments actually run. Nothing but the
  cleanup's own explicit child deletes can remove the child rows here, so this is
  the case that catches a regression back to "let the cascade handle it".
- `foreign_keys=ON`   mirrors PostgreSQL, where the constraints are always
  enforced. This is the case that catches a wrong delete order (a child row still
  pointing at a `drug` row we are about to remove aborts the batch).

They run against their own throwaway SQLite database rather than the session
database, so they neither depend on nor disturb the live server the other tests
share.
"""

from typing import Dict, Tuple
import asyncio
import datetime
import os
import uuid

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel, create_engine, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from medlogserver.model.__tables__ import all_tables  # noqa: F401  (registers metadata)
from medlogserver.db.drug_data.drug_search import GenericSQLDrugSearchCache
from medlogserver.model.drug_data import DrugData, DrugDataSetVersion
from medlogserver.model.drug_data.drug_attr import (
    DrugVal,
    DrugValMulti,
    DrugValMultiRef,
    DrugValRef,
)
from medlogserver.model.drug_data.drug_code import DrugCode
from medlogserver.model.intake import Intake

IMPORTER = "mmi"
CODE_SYSTEM = "PZN"

# Deliberately not a multiple of the batch size used below, so the last batch is
# a partial one and the loop has to notice on its own that it is done.
OBSOLETE_DRUG_COUNT = 120
ACTIVE_DRUG_COUNT = 10
CUSTOM_DRUG_COUNT = 5
TEST_BATCH_SIZE = 50

# every table the cleanup has to empty, keyed by the column pointing at drug.id
CHILD_MODELS = {
    "attr": (DrugVal, DrugVal.drug_id),
    "attr_ref": (DrugValRef, DrugValRef.drug_id),
    "attr_multi": (DrugValMulti, DrugValMulti.drug_id),
    "attr_multi_ref": (DrugValMultiRef, DrugValMultiRef.drug_id),
    "code": (DrugCode, DrugCode.drug_id),
    "search_cache": (GenericSQLDrugSearchCache, GenericSQLDrugSearchCache.id),
}


@pytest.fixture(params=[False, True], ids=["fk_off", "fk_on"])
def isolated_db(request, tmp_path, monkeypatch):
    """An empty MedLog schema in a throwaway SQLite file, wired into the db layer.

    `medlogserver.db._session` caches its engine in module globals, so pointing the
    cleanup at another database means replacing those. monkeypatch restores them
    when the test ends.
    """
    enforce_foreign_keys = request.param
    db_file = tmp_path / "cleanup_test.sqlite"

    SQLModel.metadata.create_all(create_engine(f"sqlite:///{db_file}"))

    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_file}",
        future=True,
        # every test drives its own asyncio.run(), so pooled connections must not
        # outlive the loop that opened them
        poolclass=NullPool,
    )
    if enforce_foreign_keys:

        @event.listens_for(engine.sync_engine, "connect")
        def _enable_foreign_keys(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    from medlogserver.db import _session

    monkeypatch.setattr(_session, "_db_engine", engine)
    monkeypatch.setattr(
        _session,
        "_async_session_factory",
        sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False),
    )
    # _get_engine()/_get_session_factory() rebuild their globals whenever
    # _engine_pid does not match the current process. Pinning it to this process
    # is what keeps them from throwing our objects away and reconnecting to the
    # session database named in the config.
    monkeypatch.setattr(_session, "_engine_pid", os.getpid())

    yield engine

    asyncio.run(engine.dispose())


def _drug_dataset(version: str, current_active: bool) -> DrugDataSetVersion:
    return DrugDataSetVersion(
        id=uuid.uuid4(),
        dataset_version=version,
        dataset_source_name="MMI Pharmindex",
        dataset_link=None,
        is_custom_drugs_collection=False,
        current_active=current_active,
        import_status="done",
        import_start_datetime_utc=datetime.datetime.now(datetime.UTC),
    )


async def _seed(session) -> Tuple[DrugDataSetVersion, DrugDataSetVersion, DrugDataSetVersion, uuid.UUID]:
    """Build three dataset versions and return them plus the drug held by an intake.

    Rows are committed parent-before-child so the seed also survives with foreign
    key enforcement switched on.
    """
    from medlogserver.model.drug_data.drug_attr_field_definition import (
        DrugAttrFieldDefinition,
    )
    from medlogserver.model.drug_data.drug_attr_field_lov_item import DrugAttrFieldLovItem
    from medlogserver.model.drug_data.drug_code_system import DrugCodeSystem
    from medlogserver.model.event import Event
    from medlogserver.model.interview import Interview
    from medlogserver.model.study import Study
    from medlogserver.model.user import User

    obsolete = _drug_dataset("v_old", current_active=False)
    active = _drug_dataset("v_new", current_active=True)
    custom = _drug_dataset("custom", current_active=False)
    custom.is_custom_drugs_collection = True
    session.add_all([obsolete, active, custom])
    await session.commit()

    session.add(
        DrugCodeSystem(
            id=CODE_SYSTEM, name="Pharmazentralnummer", country="Germany", importer_name=IMPORTER
        )
    )
    for field_name, is_ref, is_multi in (
        ("plain", False, False),
        ("ref", True, False),
        ("multi", False, True),
        ("multi_ref", True, True),
    ):
        session.add(
            DrugAttrFieldDefinition(
                field_name=field_name,
                field_name_display=field_name,
                importer_name=IMPORTER,
                is_reference_list_field=is_ref,
                is_multi_val_field=is_multi,
            )
        )
    await session.commit()

    # the ref/multi_ref values point at list-of-value items of their own dataset
    for dataset in (obsolete, active, custom):
        for field_name in ("ref", "multi_ref"):
            session.add(
                DrugAttrFieldLovItem(
                    field_name=field_name,
                    importer_name=IMPORTER,
                    value="lov_value",
                    display="LOV value",
                    drug_dataset_version_fk=dataset.id,
                )
            )
    await session.commit()

    user = User(id=uuid.uuid4(), user_name="cleanup-test-user")
    study = Study(id=uuid.uuid4(), display_name="Cleanup Test Study")
    session.add_all([user, study])
    await session.commit()
    event_row = Event(id=uuid.uuid4(), name="Cleanup Test Event", study_id=study.id)
    session.add(event_row)
    await session.commit()
    interview = Interview(
        id=uuid.uuid4(),
        event_id=event_row.id,
        interviewer_user_id=user.id,
        proband_external_id="AAA1111",
        interview_start_time_utc=datetime.datetime.now(datetime.UTC),
        proband_has_taken_meds=True,
    )
    session.add(interview)
    await session.commit()

    drug_held_by_intake = None
    drugs = []
    for dataset, count in (
        (obsolete, OBSOLETE_DRUG_COUNT),
        (active, ACTIVE_DRUG_COUNT),
        (custom, CUSTOM_DRUG_COUNT),
    ):
        for i in range(count):
            drug = DrugData(
                id=uuid.uuid4(),
                source_dataset_id=dataset.id,
                trade_name=f"Drug {i}",
                is_custom_drug=False,
                custom_drug_notes=None,
            )
            drugs.append((drug, dataset, i))
            session.add(drug)
            if dataset is obsolete and i == 0:
                drug_held_by_intake = drug.id
    await session.commit()

    for drug, dataset, i in drugs:
        session.add(
            DrugVal(drug_id=drug.id, field_name="plain", value="v", importer_name=IMPORTER)
        )
        session.add(
            DrugValRef(
                drug_id=drug.id,
                field_name="ref",
                value="lov_value",
                importer_name=IMPORTER,
                drug_dataset_version_fk=dataset.id,
            )
        )
        session.add(
            DrugValMulti(
                drug_id=drug.id,
                field_name="multi",
                value_index=0,
                value="v",
                importer_name=IMPORTER,
            )
        )
        session.add(
            DrugValMultiRef(
                drug_id=drug.id,
                field_name="multi_ref",
                value_index=0,
                value="lov_value",
                importer_name=IMPORTER,
                drug_dataset_version_fk=dataset.id,
            )
        )
        session.add(
            DrugCode(
                id=uuid.uuid4(),
                drug_id=drug.id,
                code_system_id=CODE_SYSTEM,
                code=str(i),
            )
        )
        session.add(
            GenericSQLDrugSearchCache(
                id=drug.id,
                search_index_content="content",
                search_cache_codes="codes",
                is_custom_drug=False,
            )
        )
    await session.commit()

    # one obsolete drug is referenced by an intake and therefore must be kept
    session.add(
        Intake(
            id=uuid.uuid4(),
            drug_id=drug_held_by_intake,
            interview_id=interview.id,
            consumed_meds_today="YES",
            is_activeingredient_equivalent_choice=False,
        )
    )
    await session.commit()

    return obsolete, active, custom, drug_held_by_intake


async def _count_drugs(session, dataset_id: uuid.UUID) -> int:
    return (
        await session.exec(
            select(func.count(DrugData.id)).where(DrugData.source_dataset_id == dataset_id)
        )
    ).one()


async def _count_children(session) -> Dict[str, int]:
    counts = {}
    for name, (model, column) in CHILD_MODELS.items():
        counts[name] = (await session.exec(select(func.count(column)))).one()
    return counts


def test_cleanup_removes_obsolete_drugs_and_all_their_child_rows(isolated_db, monkeypatch):
    """The whole obsolete dataset goes, child rows included, in more than one batch."""
    from medlogserver.db._session import get_async_session_context
    from medlogserver.worker.tasks import drug_data_remove_obsolete_drug_entries as cleaner

    monkeypatch.setattr(cleaner, "_DELETE_BATCH_SIZE", TEST_BATCH_SIZE)

    async def scenario():
        async with get_async_session_context() as session:
            obsolete, active, custom, drug_held_by_intake = await _seed(session)

        async with get_async_session_context() as session:
            assert await _count_drugs(session, obsolete.id) == OBSOLETE_DRUG_COUNT
            total_drugs = OBSOLETE_DRUG_COUNT + ACTIVE_DRUG_COUNT + CUSTOM_DRUG_COUNT
            assert await _count_children(session) == {
                name: total_drugs for name in CHILD_MODELS
            }
            # guard against a seed that silently fails to link the intake, which
            # would make the "drug must survive" assertion below meaningless
            referenced = (
                await session.exec(
                    select(func.count(DrugData.id))
                    .join(Intake, DrugData.id == Intake.drug_id)
                    .where(DrugData.source_dataset_id == obsolete.id)
                )
            ).one()
            assert referenced == 1

        finished = await cleaner.DrugDataRemoveObsoleteDrugDataEntries().drug_data_remove_obsolete_drug_entries()
        assert finished is True

        async with get_async_session_context() as session:
            # the intake-referenced drug survives, the other 119 are gone
            assert await _count_drugs(session, obsolete.id) == 1
            assert (
                await session.exec(
                    select(func.count(DrugData.id)).where(DrugData.id == drug_held_by_intake)
                )
            ).one() == 1

            # untouched datasets stay untouched
            assert await _count_drugs(session, active.id) == ACTIVE_DRUG_COUNT
            assert await _count_drugs(session, custom.id) == CUSTOM_DRUG_COUNT

            # this is the assertion tests_drug_db_updater.py is missing: no orphans
            surviving_drugs = 1 + ACTIVE_DRUG_COUNT + CUSTOM_DRUG_COUNT
            assert await _count_children(session) == {
                name: surviving_drugs for name in CHILD_MODELS
            }

            for dataset_id, should_be_cleaned in (
                (obsolete.id, True),
                (active.id, False),
                (custom.id, False),
            ):
                dataset = (
                    await session.exec(
                        select(DrugDataSetVersion).where(DrugDataSetVersion.id == dataset_id)
                    )
                ).one()
                assert (dataset.cleaned_date_datetime_utc is not None) is should_be_cleaned

    asyncio.run(scenario())


def test_cleanup_run_after_a_finished_cleanup_changes_nothing(isolated_db, monkeypatch):
    """A dataset marked cleaned is skipped, so a second run is a no-op."""
    from medlogserver.db._session import get_async_session_context
    from medlogserver.worker.tasks import drug_data_remove_obsolete_drug_entries as cleaner

    monkeypatch.setattr(cleaner, "_DELETE_BATCH_SIZE", TEST_BATCH_SIZE)

    async def scenario():
        async with get_async_session_context() as session:
            await _seed(session)

        run = cleaner.DrugDataRemoveObsoleteDrugDataEntries().drug_data_remove_obsolete_drug_entries
        assert await run() is True

        async with get_async_session_context() as session:
            after_first = (await _count_children(session), await _count_drugs_all(session))

        assert await run() is True

        async with get_async_session_context() as session:
            after_second = (await _count_children(session), await _count_drugs_all(session))

        assert after_first == after_second

    asyncio.run(scenario())


async def _count_drugs_all(session) -> int:
    return (await session.exec(select(func.count(DrugData.id)))).one()
