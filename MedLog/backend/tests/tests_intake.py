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
    dictyfy,
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
    from medlogserver.model.intake import IntakeStartDateOption

    search_identifiert_flag = "8473wterfgjhdsgf789w3eitgu"
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
            "dispensingtype": {
                "value": 0,
                "display": "prescription",
                "ref_list": "/api/drug/field_def/dispensingtype/refs",
            }
        },
        exception_dict_identifier="create custom drug object attrs_ref",
    )
    dict_must_contain(
        res["attrs_multi_ref"],
        required_keys_and_val={
            "producing_country": [
                {
                    "value": "DE",
                    "display": "Germany",
                    "ref_list": "/api/drug/field_def/producing_country/refs",
                },
                {
                    "value": "UK",
                    "display": "United Kingdom",
                    "ref_list": "/api/drug/field_def/producing_country/refs",
                },
            ]
        },
        exception_dict_identifier="create custom drug object attrs_ref",
    )
    dict_must_contain(
        res["codes"],
        required_keys_and_val={"PZN": "12345678910"},
        exception_dict_identifier="create custom drug object attrs_ref",
    )


def test_last_interview_intakes():
    """Test retrieving intakes from the last completed interview"""
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestLastIntakesStudy",
        with_events=2,
        with_interviews_per_event_per_proband=1,
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
    from medlogserver.api.routes.routes_drug import search_drugs

    drug_search_result = req("api/drug/search", q={"search_term": "Test"})
    drug = drug_search_result["items"][0]["drug"]
    from medlogserver.model.intake import (
        IntakeCreateAPI,
        SourceOfDrugInformationAnwers,
        AdministeredByDoctorAnswers,
        IntakeRegularOrAsNeededAnswers,
        ConsumedMedsTodayAnswers,
    )

    # Create a test intake
    intake_data = IntakeCreateAPI(
        drug_id=drug["id"],
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
    from medlogserver.model.intake import (
        IntakeCreateAPI,
        IntakeUpdate,
        SourceOfDrugInformationAnwers,
        AdministeredByDoctorAnswers,
        IntakeRegularOrAsNeededAnswers,
        ConsumedMedsTodayAnswers,
        IntakeStartDateOption,
    )

    update_data = IntakeUpdate(
        administered_by_doctor=AdministeredByDoctorAnswers.NO,
        intake_start_date=None,
        intake_start_date_option=IntakeStartDateOption.UNKNOWN,
    )
    print("dictyfy(update_data)", dictyfy(update_data))
    updated_intake = req(
        f"api/study/{study_id}/interview/{interview.interview.id}/intake/{intake.intake.id}",
        method="patch",
        b=dictyfy(update_data),
    )
    print("updated_intake", updated_intake)
    # Verify the update
    dict_must_contain(
        updated_intake,
        required_keys_and_val={
            "administered_by_doctor": "no",
        },
        exception_dict_identifier="update intake response",
    )


def test_get_intake():
    """Test updating an existing intake"""
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestGetIntakeStudy",
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
    from medlogserver.model.intake import (
        IntakeCreateAPI,
        IntakeUpdate,
        SourceOfDrugInformationAnwers,
        AdministeredByDoctorAnswers,
        IntakeRegularOrAsNeededAnswers,
        ConsumedMedsTodayAnswers,
    )

    # test from medlogserver.api.routes.routes_intake import get_intake

    intake = req(
        f"api/study/{study_id}/interview/{interview.interview.id}/intake/{intake.intake.id}",
        method="get",
    )

    # quick sanity check. Could be improved
    dict_must_contain(
        intake,
        required_keys=[
            "intake_start_date",
            "administered_by_doctor",
            "source_of_drug_information",
        ],
        exception_dict_identifier="get intake response",
    )


def test_create_intake_with_empty_start_date_issue_163():
    """Test creating a new intake"""
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestCreateIntakeWithEmptyStartDateStudy",
        with_events=1,
        with_interviews_per_event_per_proband=1,
        with_intakes=0,
        proband_count=1,
    )

    study_id = study_data.study.id
    event = study_data.events[0]
    interview = event.interviews[0]
    from medlogserver.api.routes.routes_drug import search_drugs

    drug_search_result = req("api/drug/search", q={"search_term": "Test"})
    drug = drug_search_result["items"][0]["drug"]
    from medlogserver.model.intake import (
        IntakeCreateAPI,
        SourceOfDrugInformationAnwers,
        AdministeredByDoctorAnswers,
        IntakeRegularOrAsNeededAnswers,
        ConsumedMedsTodayAnswers,
    )
    from medlogserver.model.intake import IntakeStartDateOption

    # Create a test intake
    intake_data = IntakeCreateAPI(
        drug_id=drug["id"],
        source_of_drug_information=SourceOfDrugInformationAnwers.DRUG_LEAFLET,
        intake_start_date=None,
        intake_start_date_option=IntakeStartDateOption.UNKNOWN,
        administered_by_doctor=AdministeredByDoctorAnswers.PRESCRIBED,
        intake_regular_or_as_needed=IntakeRegularOrAsNeededAnswers.ASNEEDED,
        as_needed_dose_unit=1,
        consumed_meds_today=ConsumedMedsTodayAnswers.UNKNOWN,
    )
    intake_data_dict = dictyfy(intake_data)
    from medlogserver.api.routes.routes_intake import create_intake

    new_intake: Dict = req(
        f"api/study/{study_id}/interview/{interview.interview.id}/intake",
        method="post",
        b=intake_data_dict,
    )

    # Verify the created intake
    dict_must_contain(
        new_intake,
        required_keys_and_val={"intake_start_date": None},
        exception_dict_identifier="create intake with empty start time response",
    )


def test_create_intake_with_special_dateoptions_issue_215():
    # https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues/215
    """Test creating a new intake"""
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestCreateIntakeWithSpecialStartDateStudy",
        with_events=1,
        with_interviews_per_event_per_proband=1,
        with_intakes=0,
        proband_count=1,
    )

    study_id = study_data.study.id
    event = study_data.events[0]
    interview = event.interviews[0]
    from medlogserver.api.routes.routes_drug import search_drugs

    drug_search_result = req("api/drug/search", q={"search_term": "Test"})
    drug = drug_search_result["items"][0]["drug"]
    from medlogserver.model.intake import (
        IntakeCreateAPI,
        SourceOfDrugInformationAnwers,
        AdministeredByDoctorAnswers,
        IntakeRegularOrAsNeededAnswers,
        ConsumedMedsTodayAnswers,
        IntakeEndDateOption,
        IntakeStartDateOption,
    )

    # Create a test intake
    intake_data = IntakeCreateAPI(
        drug_id=drug["id"],
        source_of_drug_information=SourceOfDrugInformationAnwers.DRUG_LEAFLET,
        intake_start_date=None,
        intake_start_date_option=IntakeStartDateOption.AT_LEAST_12_MONTHS,
        intake_end_date_option=IntakeEndDateOption.ONGOING,
        administered_by_doctor=AdministeredByDoctorAnswers.PRESCRIBED,
        intake_regular_or_as_needed=IntakeRegularOrAsNeededAnswers.ASNEEDED,
        as_needed_dose_unit=1,
        consumed_meds_today=ConsumedMedsTodayAnswers.UNKNOWN,
    )
    intake_data_dict = dictyfy(intake_data)
    from medlogserver.api.routes.routes_intake import create_intake

    new_intake: Dict = req(
        f"api/study/{study_id}/interview/{interview.interview.id}/intake",
        method="post",
        b=intake_data_dict,
    )

    # Verify the created intake
    dict_must_contain(
        new_intake,
        required_keys_and_val={
            "intake_start_date": None,
            "intake_start_date_option": IntakeStartDateOption.AT_LEAST_12_MONTHS.value,
            "intake_end_date_option": IntakeEndDateOption.ONGOING.value,
        },
        exception_dict_identifier="create intake with empty start time response",
    )


def test_create_intake_with_end_and_start_option_update_issue_228():
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestCreateIntakeWithEndAndStartOption228",
        with_events=1,
        with_interviews_per_event_per_proband=1,
        with_intakes=0,
        proband_count=1,
    )

    study_id = study_data.study.id
    event = study_data.events[0]
    interview = event.interviews[0]
    from medlogserver.api.routes.routes_drug import search_drugs

    drug_search_result = req("api/drug/search", q={"search_term": "Test"})
    drug = drug_search_result["items"][0]["drug"]
    from medlogserver.model.intake import (
        IntakeCreateAPI,
        IntakeUpdate,
        SourceOfDrugInformationAnwers,
        AdministeredByDoctorAnswers,
        IntakeRegularOrAsNeededAnswers,
        ConsumedMedsTodayAnswers,
        IntakeEndDateOption,
        IntakeStartDateOption,
    )

    # Create an intake with both start and end date options
    intake_data = IntakeCreateAPI(
        drug_id=drug["id"],
        source_of_drug_information=SourceOfDrugInformationAnwers.DRUG_LEAFLET,
        intake_end_date_option=IntakeEndDateOption.ONGOING,
        intake_start_date_option=IntakeStartDateOption.AT_LEAST_12_MONTHS,
        administered_by_doctor=AdministeredByDoctorAnswers.PRESCRIBED,
        intake_regular_or_as_needed=IntakeRegularOrAsNeededAnswers.ASNEEDED,
        as_needed_dose_unit=1,
        consumed_meds_today=ConsumedMedsTodayAnswers.UNKNOWN,
    )
    intake_data_dict = dictyfy(intake_data)
    from medlogserver.api.routes.routes_intake import create_intake

    new_intake: Dict = req(
        f"api/study/{study_id}/interview/{interview.interview.id}/intake",
        method="post",
        b=intake_data_dict,
    )

    dict_must_contain(
        new_intake,
        required_keys_and_val={
            "intake_start_date": None,
            "intake_end_date": None,
            "intake_start_date_option": IntakeStartDateOption.AT_LEAST_12_MONTHS.value,
            "intake_end_date_option": IntakeEndDateOption.ONGOING.value,
        },
        exception_dict_identifier="create intake with empty start time response",
    )

    # Send a PATCH request to set start and end dates (omit options)
    today_date_string = datetime.date.today().isoformat()
    tomorrow_date_string = (
        datetime.date.today() + datetime.timedelta(days=1)
    ).isoformat()
    intake_data_update_dict = {
        "intake_start_date": today_date_string,
        "intake_end_date": tomorrow_date_string,
    }

    updated_intake_resp = req(
        f"api/study/{study_id}/interview/{interview.interview.id}/intake/{new_intake['id']}",
        method="patch",
        b=intake_data_update_dict,
    )
    # Verify the updated intake
    # because we set a date, the options should be automactly set to none by the backend
    dict_must_contain(
        updated_intake_resp,
        required_keys_and_val={
            "intake_start_date": today_date_string,
            "intake_end_date": tomorrow_date_string,
            "intake_start_date_option": None,
            "intake_end_date_option": None,
        },
        exception_dict_identifier="create intake with empty start time response",
    )

    intake_data_update_dict = {
        "intake_start_date_option": IntakeStartDateOption.AT_LEAST_12_MONTHS.value,
    }
    updated_intake_resp = req(
        f"api/study/{study_id}/interview/{interview.interview.id}/intake/{new_intake['id']}",
        method="patch",
        b=intake_data_update_dict,
    )
    dict_must_contain(
        updated_intake_resp,
        required_keys_and_val={
            "intake_start_date": None,
            "intake_end_date": tomorrow_date_string,
            "intake_start_date_option": IntakeStartDateOption.AT_LEAST_12_MONTHS.value,
            "intake_end_date_option": None,
        },
        exception_dict_identifier="create intake with empty start time response",
    )
