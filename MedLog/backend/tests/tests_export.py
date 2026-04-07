from typing import List, Dict
import json
import time
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
    is_valid_csv_with_rows,
    dictyfy,
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
        trade_name=f"My Custom Drug with refs {search_identifiert_flag}",
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
        intake_start_date=datetime.date.today().isoformat(),
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
