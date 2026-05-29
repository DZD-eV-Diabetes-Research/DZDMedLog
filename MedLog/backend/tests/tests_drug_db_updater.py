from typing import Any, List, Dict, cast
import json
import time
import datetime


from utils import (
    req,
    dict_must_contain,
    dictyfy,
    create_test_study,
    TestDataContainerStudy,
)


def test_endpoint_drug_update_status():
    """Test GET /api/drug/db/update endpoint"""
    from medlogserver.api.routes.routes_drug_db_updater import get_drug_update_status
    from medlogserver.model.drug_updater_status import DrugUpdaterStatus

    response: Dict[str, Any] = req("api/drug/db/update", method="get")
    print(f"test_endpoint_drug_update_status response: {response}")

    dict_must_contain(
        response,
        required_keys_and_val={
            "update_available": True,
            "update_available_version": "20251228",
            "update_running": False,
            "last_update_run_error": None,
            "current_drug_data_version": "20241126",
            "current_drug_data_ready_to_use": True,
        },
        required_keys=["last_update_run_datetime_utc", "current_drug_data_version"],
        exception_dict_identifier="version response",
    )


def test_endpoint_drug_update_workflow():
    """This tests a complete workflow. updating the drugdatabase and validate everything for sanity
    This must be done in large test as we have a lot of state handling/validation during this process
    """
    from medlogserver.api.routes.routes_drug_db_updater import (
        trigger_drug_update_active,
    )
    from medlogserver.model.drug_updater_status import DrugUpdaterStatus

    #####
    # PREPS
    ####

    # get and store drugs from current dataset currents to validate change later
    # DrugToProveIntialDataset1
    # DrugToProveIntialDatasetCleaned2
    drug_search_response: Dict[str, Any] = req(
        "api/drug/search", method="get", q={"search_term": "DrugToProveIntialDataset1"}
    )
    drug_to_prove_inital_dataset = drug_search_response["items"][0]["drug"]
    from medlogserver.api.routes.routes_drug import DrugAPIRead

    assert drug_to_prove_inital_dataset["trade_name"] == "DrugToProveIntialDataset1"
    drug_search_response: Dict[str, Any] = req(
        "api/drug/search",
        method="get",
        q={"search_term": "DrugToProveIntialDatasetCleaned2"},
    )
    drug_to_prove_inital_dataset_was_cleaned = drug_search_response["items"][0]["drug"]
    assert (
        drug_to_prove_inital_dataset_was_cleaned["trade_name"]
        == "DrugToProveIntialDatasetCleaned2"
    )

    #####
    # Use one drug of current dataset
    #####

    study_data: TestDataContainerStudy = create_test_study(
        study_name="test_endpoint_drug_update_workflow_study",
        with_events=1,
        with_interviews_per_event_per_proband=1,
        with_intakes=0,
        proband_count=1,
    )
    study_id = study_data.study.id
    event = study_data.events[0]
    interview = event.interviews[0]

    from medlogserver.model.intake import (
        IntakeCreateAPI,
        SourceOfDrugInformationAnwers,
        AdministeredByDoctorAnswers,
        IntakeRegularOrAsNeededAnswers,
        ConsumedMedsTodayAnswers,
    )

    # Create a test intake
    intake_data = IntakeCreateAPI(
        drug_id=drug_to_prove_inital_dataset["id"],
        source_of_drug_information=SourceOfDrugInformationAnwers.DRUG_LEAFLET,
        intake_start_date=datetime.date.today().isoformat(),
        administered_by_doctor=AdministeredByDoctorAnswers.PRESCRIBED,
        intake_regular_or_as_needed=IntakeRegularOrAsNeededAnswers.ASNEEDED,
        as_needed_dose_unit=1,
        consumed_meds_today=ConsumedMedsTodayAnswers.UNKNOWN,
    )
    intake_data_dict = dictyfy(intake_data)
    from medlogserver.api.routes.routes_intake import create_intake

    new_intake = req(
        f"api/study/{study_id}/interview/{interview.interview.id}/intake",
        method="post",
        b=intake_data_dict,
    )

    #####
    # Trigger the update
    #####
    from medlogserver.api.routes.routes_drug_db_updater import (
        trigger_drug_update_active,
    )

    response: Dict[str, Any] = req(
        "api/drug/db/update", method="put", expected_http_code=201
    )

    print("api/drug/db/update response:", response)
    dict_must_contain(
        response,
        required_keys_and_val={
            "update_available": False,
            "update_available_version": None,
            "update_running": True,
            "last_update_run_error": None,
            "current_drug_data_version": "20241126",
            "current_drug_data_ready_to_use": True,
        },
        required_keys=["last_update_run_datetime_utc"],
        exception_dict_identifier="test_endpoint_drug_update_trigger response",
    )
    # hammer the update-start trigger a second time to check if it does not accidentiale trigger a second overlapping update process
    response_2: Dict[str, Any] = req(
        "api/drug/db/update", method="put", expected_http_code=200
    )
    dict_must_contain(
        response,
        required_keys_and_val={
            "update_running": True,
        },
        exception_dict_identifier="test_endpoint_drug_update_trigger second response",
    )

    #####
    # Wait for the update to be finished
    #####

    update_running = True
    timeout_seconds = 60
    start_time = time.time()
    while update_running:
        if time.time() - start_time > timeout_seconds:
            raise TimeoutError(
                f"Drug DB update did not complete within {timeout_seconds} seconds"
            )
        response_status: Dict[str, Any] = req("api/drug/db/update", method="get")
        print(f"test_endpoint_drug_update_trigger response_status: {response}")
        dict_must_contain(
            response_status,
            required_keys_and_val={"last_update_run_error": None},
            required_keys=["update_running"],
            exception_dict_identifier="test_endpoint_drug_update_trigger loop response",
        )
        update_running = response_status["update_running"]
        print("WAIT FOR UPDATE update_running:", update_running)
        time.sleep(2)

    #####
    # Validate update status
    #####

    time.sleep(2)
    response: Dict[str, Any] = req("api/drug/db/update", method="get")
    print("response", response)
    dict_must_contain(
        response,
        required_keys_and_val={
            "update_available": False,
            "update_available_version": None,
            "update_running": False,
            "last_update_run_error": None,
            "current_drug_data_version": "20251228",
            "current_drug_data_ready_to_use": True,
        },
        required_keys=["last_update_run_datetime_utc", "current_drug_data_version"],
        exception_dict_identifier="test_endpoint_drug_update_trigger response",
    )

    #####
    # Wait for cleaner job done
    #####
    response_cleaner_job = None
    cleaning_running = True
    while cleaning_running:
        from medlogserver.api.routes.routes_debug import list_all_worker_jobs

        response_cleaner_job: List[Dict] = cast(
            List[Dict],
            req(
                "api/debug/worker/job",
                method="get",
                q={"filter_tags": ["triggeredBy:drug-data-loader/version:20251228"]},
            ),
        )
        print(
            f"test_endpoint_drug_update_trigger response_status: {response_cleaner_job}"
        )
        if len(response_cleaner_job) == 0:
            continue
        from medlogserver.api.routes.routes_debug import WorkerJob

        if response_cleaner_job[0]["run_finished_at"] is not None:
            cleaning_running = False
        print("WAIT FOR CLEANING JOB cleaning_running:", cleaning_running)
        time.sleep(2)

    if response_cleaner_job[0]["last_error"] is not None:
        print(response_cleaner_job[0]["last_error"])
        raise ValueError("Obsolete Drugdata set cleaning Job failed")

    #####
    # Validate Cleaner
    #####
    # we expect the drug from the replaced dataset that was connected to an intake to be still existent but the un-used drug to re wiped
    from medlogserver.api.routes.routes_drug import get_drug

    # this drug is from an obsolete dataset, but still must be keeped in the database because it was used in an intake
    response_post_cleaner_drug_to_prove_inital_dataset: Dict[str, Any] = cast(
        Dict[str, Any],
        req(
            f"/api/drug/id/{drug_to_prove_inital_dataset['id']}",
            method="get",
            expected_http_code=200,
        ),
    )
    # this drug is from an obsolete dataset and was never used. Therefore it must be deleted by the cleaning job
    response_post_cleaner_drug_to_prove_inital_dataset_was_cleaned: Dict[str, Any] = (
        cast(
            Dict[str, Any],
            req(
                f"/api/drug/id/{drug_to_prove_inital_dataset_was_cleaned['id']}",
                method="get",
                expected_http_code=404,
            ),
        )
    )

    list_dispensingtype = req(
        "/api/drug/field_def/dispensingtype/refs",
        method="get",
    )

    def find_duplicates(dict_list):
        seen = set()
        duplicates = []

        for d in dict_list:
            key = tuple(sorted(d.items()))
            if key in seen:
                duplicates.append(d)
            else:
                seen.add(key)

        return duplicates

    if find_duplicates(list_dispensingtype["items"]):
        raise ValueError(
            f"Duplicated in ref values for dispensingtype after second drug update: {list_dispensingtype}"
        )
    # print("list_dispensingtype", list_dispensingtype)


def test_drug_data_cleaning_memory_and_correctness():
    """Regression test for the ObsoleteDrugEntries cleaner.

    Bugs being guarded:
    1. `DrugDataSetVersion.cleaned_date_datetime_utc = ...` set the *class* attribute
       instead of the instance — the DB record was never marked cleaned, so every
       run reprocessed all old datasets from scratch (infinite CPU/disk/OOM loop).
    2. `select(DrugData)` with `lazy="selectin"` relationships loaded every drug
       row plus all its attrs/codes into Python memory, exhausting RAM on a full
       drug dataset (100 k+ entries × multiple attribute tables).
    """
    import asyncio
    import tracemalloc
    import uuid
    import datetime as dt
    from sqlmodel import select
    from medlogserver.db._session import get_async_session_context
    from medlogserver.model.drug_data import DrugData, DrugDataSetVersion
    from medlogserver.worker.tasks.drug_data_remove_obsolete_drug_entries import (
        DrugDataRemoveObsoleteDrugDataEntries,
    )

    DRUG_COUNT = 5_000

    async def run():
        dataset_id = uuid.uuid4()

        # --- Setup: one deactivated dataset with many orphaned drug entries ---
        async with get_async_session_context() as session:
            session.add(
                DrugDataSetVersion(
                    id=dataset_id,
                    dataset_version="19000101_memtest",
                    dataset_source_name="test_memtest",
                    dataset_link=None,
                    is_custom_drugs_collection=False,
                    current_active=False,
                    cleaned_date_datetime_utc=None,
                    import_status="done",
                    import_start_datetime_utc=dt.datetime.now(dt.timezone.utc),
                )
            )
            await session.flush()
            for i in range(DRUG_COUNT):
                session.add(
                    DrugData(
                        source_dataset_id=dataset_id,
                        trade_name=f"MemTestDrug{i:05d}",
                    )
                )
            await session.commit()

        # --- Run the cleaner while tracking Python memory allocations ---
        tracemalloc.start()
        await DrugDataRemoveObsoleteDrugDataEntries().drug_data_remove_obsolete_drug_entries()
        _current, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # --- Verify correctness: all orphaned drugs must be deleted ---
        async with get_async_session_context() as session:
            remaining_drugs = (
                await session.exec(
                    select(DrugData).where(DrugData.source_dataset_id == dataset_id)
                )
            ).all()
            dataset_after = (
                await session.exec(
                    select(DrugDataSetVersion).where(DrugDataSetVersion.id == dataset_id)
                )
            ).one()

        return peak_bytes, len(remaining_drugs), dataset_after.cleaned_date_datetime_utc

    peak_bytes, remaining_count, cleaned_at = asyncio.run(run())

    # All orphaned drugs must have been deleted
    assert remaining_count == 0, (
        f"Expected 0 remaining drugs after cleaning, got {remaining_count}. "
        "The cleaner may not be deleting orphaned entries."
    )

    # cleaned_date_datetime_utc must be written to the DB instance, not the class.
    # If it's None the dataset would be re-processed on every future run.
    assert cleaned_at is not None, (
        "DrugDataSetVersion.cleaned_date_datetime_utc was not persisted. "
        "The cleaner is setting the class attribute instead of the instance attribute, "
        "which causes every run to reprocess all old datasets (infinite OOM loop)."
    )

    # Peak Python memory must not scale with the number of drug records.
    # Generous 30 MB cap — the fixed implementation loads no DrugData objects.
    # The broken implementation would load DRUG_COUNT ORM objects + all their
    # selectin-loaded relationship collections, which is several hundred MB here
    # and 16+ GB on a production-sized dataset.
    peak_mb = peak_bytes / (1024 * 1024)
    assert peak_mb < 30, (
        f"Cleaning job used {peak_mb:.1f} MB peak memory for {DRUG_COUNT} drugs "
        f"(expected < 30 MB). The implementation may be loading drug objects into "
        f"Python memory instead of using a server-side subquery."
    )


def test_drug_data_cleaning_skips_already_cleaned_datasets():
    """Cleaner must not re-process datasets that were already cleaned.

    Regression for the class-attribute bug: if cleaned_date_datetime_utc is never
    persisted the WHERE clause `IS NULL` always matches, causing re-processing.
    """
    import asyncio
    import uuid
    import datetime as dt
    from sqlmodel import select
    from medlogserver.db._session import get_async_session_context
    from medlogserver.model.drug_data import DrugData, DrugDataSetVersion
    from medlogserver.worker.tasks.drug_data_remove_obsolete_drug_entries import (
        DrugDataRemoveObsoleteDrugDataEntries,
    )

    async def run():
        dataset_id = uuid.uuid4()
        already_cleaned = dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc)

        # Create a dataset already marked as cleaned and add a drug to it
        async with get_async_session_context() as session:
            session.add(
                DrugDataSetVersion(
                    id=dataset_id,
                    dataset_version="19000102_skipmtest",
                    dataset_source_name="test_skipmtest",
                    dataset_link=None,
                    is_custom_drugs_collection=False,
                    current_active=False,
                    cleaned_date_datetime_utc=already_cleaned,
                    import_status="done",
                    import_start_datetime_utc=dt.datetime.now(dt.timezone.utc),
                )
            )
            await session.flush()
            session.add(
                DrugData(
                    source_dataset_id=dataset_id,
                    trade_name="ShouldNotBeDeleted",
                )
            )
            await session.commit()

        # Run cleaner — should not touch the already-cleaned dataset
        await DrugDataRemoveObsoleteDrugDataEntries().drug_data_remove_obsolete_drug_entries()

        async with get_async_session_context() as session:
            remaining = (
                await session.exec(
                    select(DrugData).where(DrugData.source_dataset_id == dataset_id)
                )
            ).all()

        return len(remaining)

    remaining_count = asyncio.run(run())

    assert remaining_count == 1, (
        f"Already-cleaned dataset had its drug deleted (got {remaining_count} remaining). "
        "The cleaner is re-processing datasets that already have cleaned_date_datetime_utc set."
    )


def test_wrong_count_after_upgrade_issue_252():
    from medlogserver.model.drug_data.drug import (
        DrugCustomCreate,
        DrugValApiCreate,
        DrugCodeApi,
        DrugMultiValApiCreate,
    )

    custom_drug_payload = DrugCustomCreate(
        custom_drug_notes="Look mom, my custom Drug!",
        trade_name="TestCountCustom",
        codes=[DrugCodeApi(code_system_id="PZN", code="34576456745")],
        attrs=[
            DrugValApiCreate(field_name="amount", value="100"),
            DrugValApiCreate(field_name="manufacturer", value="Company1"),
        ],
        attrs_ref=[
            DrugValApiCreate(field_name="dispensingtype", value="0"),
        ],
        attrs_multi_ref=[
            DrugMultiValApiCreate(field_name="producing_country", values=["UK", "DE"])
        ],
    )
    res = req(
        "api/drug/custom",
        method="post",
        b=custom_drug_payload.model_dump(exclude_unset=True),
    )
    paginated_search_response = req(
        "api/drug/search",
        method="get",
        q={"search_term": "TestCount"},
    )

    print("paginated_search_response", paginated_search_response)
    assert paginated_search_response["total_count"] == len(
        paginated_search_response["items"]
    )
