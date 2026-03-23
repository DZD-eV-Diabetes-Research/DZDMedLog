from typing import Any, List, Dict, cast
import json
from _single_test_file_runner import run_all_tests_if_test_file_called
import time
import datetime

if __name__ == "__main__":
    run_all_tests_if_test_file_called()

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
    while update_running:
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
