from typing import List, Dict
import json
import time
import datetime
from utils import (
    req,
    dict_must_contain,
    list_contains_dict_that_must_contain,
    create_test_study,
    TestDataContainerStudy,
    is_valid_csv_with_rows,
    csv_row_matches,
    dictyfy,
    utc_today_iso,
)
from statics import (
    ADMIN_USER_EMAIL,
    ADMIN_USER_NAME,
)


def test_export_contains_with_custom_drug_issue_263():

    search_identifiert_flag = "test_export_contains_with_custom_drug_issue_263"
    # --------------------------------------------------
    # Setup: create study with minimal required structure
    # --------------------------------------------------
    study_data: TestDataContainerStudy = create_test_study(
        study_name=f"TextExportStudy {search_identifiert_flag}",
        with_events=1,
        with_interviews_per_event_per_proband=1,
        with_intakes=2,
    )
    # --------------------------------------------------
    # Step 1: Create a custom drug
    # --------------------------------------------------
    from medlogserver.model.drug_data.drug import (
        DrugCustomCreate,
    )

    custom_drug_payload = DrugCustomCreate(
        trade_name=f"My Custom Drug {search_identifiert_flag}",
    )

    custom_drug_data = req(
        "api/drug/custom",
        method="post",
        b=dictyfy(custom_drug_payload),
    )
    print("res", custom_drug_data)
    dict_must_contain(
        custom_drug_data,
        required_keys_and_val={
            "trade_name": custom_drug_payload.trade_name,
        },
        exception_dict_identifier="create minimal custom drug object",
    )
    # --------------------------------------------------
    # Step 2: Create an intake using the custom drug
    # --------------------------------------------------
    from medlogserver.model.intake import (
        IntakeCreateAPI,
        SourceOfDrugInformationAnwers,
        AdministeredByDoctorAnswers,
        IntakeRegularOrAsNeededAnswers,
        ConsumedMedsTodayAnswers,
    )

    intake_data = IntakeCreateAPI(
        drug_id=custom_drug_data["id"],
        source_of_drug_information=SourceOfDrugInformationAnwers.DRUG_LEAFLET,
        intake_start_date=utc_today_iso(),
        administered_by_doctor=AdministeredByDoctorAnswers.PRESCRIBED,
        intake_regular_or_as_needed=IntakeRegularOrAsNeededAnswers.ASNEEDED,
        as_needed_dose_unit=1,
        consumed_meds_today=ConsumedMedsTodayAnswers.UNKNOWN,
    )
    intake_data_dict = dictyfy(intake_data)
    from medlogserver.api.routes.routes_intake import create_intake

    new_intake = req(
        f"api/study/{study_data.study.id}/interview/{study_data.events[0].interviews[0].interview.id}/intake",
        method="post",
        b=intake_data_dict,
    )
    # --------------------------------------------------
    # Step 3: Trigger export creation (CSV)
    # --------------------------------------------------
    from medlogserver.api.routes.routes_export import create_export, ExportJob

    res = req(
        f"api/study/{study_data.study.id}/export",
        method="post",
        q={"format": "csv"},
    )
    processing_export = True
    from medlogserver.api.routes.routes_export import get_export, ExportJob

    # --------------------------------------------------
    # Step 4: Poll export status until finished
    # --------------------------------------------------
    while processing_export:
        res = req(
            f"api/study/{study_data.study.id}/export/{res['export_id']}",
            method="get",
        )
        if res["state"] not in ["queued", "running"]:
            processing_export = False
        time.sleep(1)
    # --------------------------------------------------
    # Step 5: Validate export finished successfully
    # --------------------------------------------------
    print(f"EXPORT STATUS: {res}")
    dict_must_contain(res, required_keys_and_val={"error": None, "state": "success"})
    # dict_must_contain(res,required_keys_and_val=)


def test_export_contains_drug_ids():
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TextExportStudy",
        with_events=1,
        with_interviews_per_event_per_proband=1,
        with_intakes=1,
    )
    study2_data: TestDataContainerStudy = create_test_study(
        study_name="TextExportStudy2",
        with_events=2,
        with_interviews_per_event_per_proband=1,
        with_intakes=2,
        proband_count=2,
    )
    from medlogserver.api.routes.routes_export import create_export, ExportJob

    res = req(
        f"api/study/{study2_data.study.id}/export",
        method="post",
        q={"format": "csv"},
    )
    processing_export = True
    from medlogserver.api.routes.routes_export import get_export, ExportJob

    while processing_export:
        res = req(
            f"api/study/{study2_data.study.id}/export/{res['export_id']}",
            method="get",
        )
        if res["state"] not in ["queued", "running"]:
            processing_export = False
        time.sleep(1)
    from medlogserver.api.routes.routes_export import download_export, FileResponse

    export_download: bytes = req(
        f"api/study/{study2_data.study.id}/export/{res['export_id']}/download",
        method="get",
    )
    assert is_valid_csv_with_rows(export_download.decode(), expected_row_count=8)
    print(
        f"api/study/{study2_data.study.id}/export/{res['export_id']}/download:\n",
        str(export_download.decode()),
    )


def test_export_multi_ref_code_values():

    search_identifiert_flag = "test_export_multi_ref_code_values"
    # --------------------------------------------------
    # Setup: create study with minimal required structure
    # --------------------------------------------------
    study_data: TestDataContainerStudy = create_test_study(
        study_name=f"TextExportStudy {search_identifiert_flag}",
        with_events=1,
        with_interviews_per_event_per_proband=1,
        with_intakes=1,
    )
    # --------------------------------------------------
    # Step 1: Create a custom drug
    # --------------------------------------------------
    from medlogserver.model.drug_data.drug import (
        DrugCustomCreate,
        DrugMultiValApiCreate,
    )

    custom_drug_payload = DrugCustomCreate(
        trade_name=f"My Custom Drug with refs {search_identifiert_flag}",
        attrs_multi_ref=[
            DrugMultiValApiCreate(field_name="producing_country", values=["DE", "UK"])
        ],
    )

    custom_drug_data = req(
        "api/drug/custom",
        method="post",
        b=dictyfy(custom_drug_payload),
    )
    print("res", custom_drug_data)
    dict_must_contain(
        custom_drug_data,
        required_keys_and_val={
            "trade_name": custom_drug_payload.trade_name,
        },
        exception_dict_identifier="create minimal custom drug object",
    )
    # --------------------------------------------------
    # Step 2: Create an intake using the custom drug
    # --------------------------------------------------
    from medlogserver.model.intake import (
        IntakeCreateAPI,
        SourceOfDrugInformationAnwers,
        AdministeredByDoctorAnswers,
        IntakeRegularOrAsNeededAnswers,
        ConsumedMedsTodayAnswers,
    )

    intake_data = IntakeCreateAPI(
        drug_id=custom_drug_data["id"],
        source_of_drug_information=SourceOfDrugInformationAnwers.DRUG_LEAFLET,
        intake_start_date=utc_today_iso(),
        administered_by_doctor=AdministeredByDoctorAnswers.PRESCRIBED,
        intake_regular_or_as_needed=IntakeRegularOrAsNeededAnswers.ASNEEDED,
        as_needed_dose_unit=1,
        consumed_meds_today=ConsumedMedsTodayAnswers.UNKNOWN,
    )
    intake_data_dict = dictyfy(intake_data)
    from medlogserver.api.routes.routes_intake import create_intake

    new_intake = req(
        f"api/study/{study_data.study.id}/interview/{study_data.events[0].interviews[0].interview.id}/intake",
        method="post",
        b=intake_data_dict,
    )
    # --------------------------------------------------
    # Step 3: Trigger export creation (CSV)
    # --------------------------------------------------
    from medlogserver.api.routes.routes_export import create_export, ExportJob

    res = req(
        f"api/study/{study_data.study.id}/export",
        method="post",
        q={"format": "csv"},
    )
    processing_export = True
    from medlogserver.api.routes.routes_export import get_export, ExportJob

    # --------------------------------------------------
    # Step 4: Poll export status until finished
    # --------------------------------------------------
    while processing_export:
        res = req(
            f"api/study/{study_data.study.id}/export/{res['export_id']}",
            method="get",
        )
        if res["state"] not in ["queued", "running"]:
            processing_export = False
        time.sleep(1)
    # --------------------------------------------------
    # Step 5: Validate export finished successfully
    # --------------------------------------------------
    print(f"EXPORT STATUS: {res}")
    dict_must_contain(
        res,
        required_keys_and_val={"error": None, "state": "success"},
        required_keys=["download_file_path"],
    )
    export_download: bytes = req(
        res["download_file_path"],
        method="get",
    )
    print(f"{res['download_file_path']}\n", str(export_download.decode()), "\n")
    assert is_valid_csv_with_rows(export_download.decode(), expected_row_count=4)
    # --------------------------------------------------
    # Step 6: Validate multi ref values have display and reference value
    # --------------------------------------------------
    csv_row_matches(
        csv_string=export_download.decode(),
        criteria={
            "drug_attr_value_producing_country": "['Germany', 'United Kingdom']",
            "drug_attr_reference_code_producing_country": "['DE', 'UK']",
        },
    )
    # dict_must_contain(res,required_keys_and_val=)


def _wait_for_export(study_id: str, export_id: str, timeout_sec: int = 60) -> Dict:
    """Poll an export job until it leaves the queued/running states."""
    deadline = time.time() + timeout_sec
    res = req(f"api/study/{study_id}/export/{export_id}", method="get")
    while res["state"] in ["queued", "running"]:
        assert time.time() < deadline, (
            f"Export job {export_id} did not finish within {timeout_sec}s: {res}"
        )
        time.sleep(1)
        res = req(f"api/study/{study_id}/export/{export_id}", method="get")
    return res


def test_export_of_deactivated_study_issue_353():
    """Issue #353: an export of a deactivated study must run through and be downloadable.

    A deactivated study is closed for data collection but stays readable, and exporting
    an archived study is exactly what one wants at the end of a study. Two places looked
    the study up without `show_deactivated=True` and therefore got `None`:

    * the export worker (`StudyDataExporter._get_study_data`) - the job died with
      "'NoneType' object has no attribute 'model_dump'" and the export never finished,
    * the download endpoint, which builds the attachment file name from the study's
      display name - it blew up with a 500 for the same reason.
    """
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestExportDeactivatedStudy",
        with_events=1,
        with_interviews_per_event_per_proband=1,
        with_intakes=1,
        proband_count=1,
    )
    study_id = str(study_data.study.id)

    req(f"api/study/{study_id}", method="patch", b={"deactivated": True})

    # Creating an export job on a deactivated study stays allowed (issue #197)
    export_job = req(f"api/study/{study_id}/export", method="post", q={"format": "csv"})

    finished_job = _wait_for_export(study_id, export_job["export_id"])
    dict_must_contain(
        finished_job,
        required_keys_and_val={"error": None, "state": "success"},
        required_keys=["download_file_path"],
        exception_dict_identifier="export job of a deactivated study",
    )

    # ... and the result can actually be downloaded
    export_download: bytes = req(finished_job["download_file_path"], method="get")
    assert is_valid_csv_with_rows(export_download.decode(), expected_row_count=1)
    csv_row_matches(
        csv_string=export_download.decode(),
        criteria={"study_display_name": "TestExportDeactivatedStudy"},
    )
