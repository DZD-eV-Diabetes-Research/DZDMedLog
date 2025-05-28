from typing import List, Dict
import json
import datetime
from _single_test_file_runner import run_all_tests_if_test_file_called

if __name__ == "__main__":
    run_all_tests_if_test_file_called()

from utils import (
    req,
    dict_must_contain,
    list_contains_dict_that_must_contain,
    create_test_study,
    TestDataContainerStudy,
)

from statics import (
    ADMIN_USER_EMAIL,
    ADMIN_USER_NAME,
)


# import only as IDE Shortcut
import medlogserver.api.routes.routes_drug


def test_do_drugv2():
    # import only as IDE Shortcut
    from medlogserver.api.routes.routes_drug import create_custom_drug
    from medlogserver.model.drug_data.drug import (
        DrugCustomCreate,
        DrugValApiCreate,
        DrugCodeApi,
        DrugValRef,
        DrugMultiValApiCreate,
    )
    from medlogserver.model.drug_data.drug import DrugData

    custom_drug_payload = DrugCustomCreate(
        custom_drug_notes="Look mom, my custom Drug!",
        trade_name=f"My Custom Drug {search_identifiert_flag}",
        codes=[DrugCodeApi(code_system_id="PZN", code="12345678910")],
        attrs=[
            DrugValApiCreate(field_name="amount", value="100"),
            DrugValApiCreate(field_name="manufacturer", value="MyHomeLab"),
        ],
        attrs_ref=[
            DrugValApiCreate(field_name="dispensingtype", value="0"),
        ],
        attrs_multi=[
            DrugMultiValApiCreate(
                field_name="keywords", value=["homemade", "custom", "test"]
            ),
        ],
        attrs_multi_ref=[
            DrugMultiValApiCreate(field_name="producing_country", values=["DE", "UK"])
        ],
    )
    print("custom_drug_payload", custom_drug_payload)
    res = req(
        "api/drug/custom",
        method="post",
        b=custom_drug_payload.model_dump(exclude_unset=True),
    )
    print("res", res)
    dict_must_contain(
        res,
        required_keys_and_val={
            "trade_name": custom_drug_payload.trade_name,
            "custom_drug_notes": custom_drug_payload.custom_drug_notes,
            "is_custom_drug": True,
        },
        required_keys=["codes", "attrs", "attrs_multi_ref"],
        exception_dict_identifier="create custom drug object",
    )
    dict_must_contain(
        res["attrs_ref"],
        required_keys_and_val={
            "hersteller": {
                "value": "225",
                "display": "Hexal AG",
                "ref_list": "/api/drug/field_def/hersteller/refs",
            }
        },
        exception_dict_identifier="create custom drug object attrs_ref",
    )
    dict_must_contain(
        res["attrs_multi_ref"],
        required_keys_and_val={
            "keywords": [
                {
                    "value": 1,
                    "display": "Mund, Zähne",
                    "ref_list": "/api/drug/field_def/keywords/refs",
                },
                {
                    "value": 4,
                    "display": "Munddesinfizientien",
                    "ref_list": "/api/drug/field_def/keywords/refs",
                },
            ]
        },
        exception_dict_identifier="create custom drug object attrs_ref",
    )
    dict_must_contain(
        res["codes"],
        required_keys_and_val={"ATC": None, "PZN": "12345678910", "MMIP": None},
        exception_dict_identifier="create custom drug object attrs_ref",
    )


def test_last_interview_intakes():
    """Test retrieving intakes from the last completed interview"""
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestLastIntakesStudy",
        with_events=2,
        with_interviews_per_event_per_proband=2,
        with_intakes=1,
        proband_count=1,
        deterministic=True,
    )

    study_id = study_data.study.id
    penultimate_event = study_data.events[0]
    last_event = study_data.events[1]
    interview1_id = penultimate_event.interviews[0].interview.id
    interview2_id = last_event.interviews[0].interview.id
    proband_id = penultimate_event.interviews[0].interview.proband_external_id
    drug_id = str(penultimate_event.interviews[0].intakes[0].drug.id)

    # Complete the first interview
    interview1 = req(
        f"api/study/{study_id}/event/{penultimate_event.event.id}/interview/{interview1_id}",
        method="patch",
        b={"interview_end_time_utc": datetime.date.today().isoformat()},
    )

    # Leave second interview incomplete
    interview2 = req(
        f"api/study/{study_id}/event/{last_event.event.id}/interview/{interview2_id}",
        method="patch",
        b={"interview_end_time_utc": None},
    )

    # Test basic last intakes endpoint
    last_intakes = req(
        f"api/study/{study_id}/proband/{proband_id}/interview/last/intake",
        method="get",
    )
    assert len(last_intakes) == 1
    assert last_intakes[0]["drug_id"] == drug_id

    # Test detailed last intakes endpoint
    last_intakes_detailed = req(
        f"api/study/{study_id}/proband/{proband_id}/interview/last/intake/details",
        method="get",
    )
    assert len(last_intakes_detailed) == 1
    assert last_intakes_detailed[0]["drug_id"] == drug_id
    assert last_intakes_detailed[0]["drug"]["id"] == drug_id


def test_create_intake():
    """Test creating a new intake"""
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestCreateIntakeStudy",
        with_events=1,
        with_interviews_per_event_per_proband=1,
        with_intakes=0,
        proband_count=1,
    )

    study_id = study_data.study.id
    event = study_data.events[0]
    interview = event.interviews[0]

    # Create a test intake
    intake_data = {
        "drug_id": "some-test-drug-id",  # You would need a valid drug ID here
        "intake_regular_or_as_needed": "regular",
        "regular_intervall_of_daily_dose": 1,
        "administered_by_doctor": False,
    }

    new_intake = req(
        f"api/study/{study_id}/event/{event.event.id}/interview/{interview.interview.id}/intake",
        method="post",
        b=intake_data,
    )

    # Verify the created intake
    dict_must_contain(
        new_intake,
        required_keys=[
            "drug_id",
            "intake_regular_or_as_needed",
            "regular_intervall_of_daily_dose",
            "administered_by_doctor",
        ],
        exception_dict_identifier="create intake response",
    )


def test_update_intake():
    """Test updating an existing intake"""
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestUpdateIntakeStudy",
        with_events=1,
        with_interviews_per_event_per_proband=1,
        with_intakes=1,
        proband_count=1,
    )

    study_id = study_data.study.id
    event = study_data.events[0]
    interview = event.interviews[0]
    intake = interview.intakes[0]

    # Update the intake
    update_data = {
        "intake_regular_or_as_needed": "as_needed",
        "administered_by_doctor": True,
    }

    updated_intake = req(
        f"api/study/{study_id}/event/{event.event.id}/interview/{interview.interview.id}/intake/{intake.intake.id}",
        method="patch",
        b=update_data,
    )

    # Verify the update
    dict_must_contain(
        updated_intake,
        required_keys_and_val={
            "intake_regular_or_as_needed": "as_needed",
            "administered_by_doctor": True,
        },
        exception_dict_identifier="update intake response",
    )
