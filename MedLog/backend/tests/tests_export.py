from typing import List, Dict
import json
import time
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
)
from statics import (
    ADMIN_USER_EMAIL,
    ADMIN_USER_NAME,
)


def test_do_export():
    return
    res = req(
        "api/study/b6f2c61b-d388-4412-8c9a-461ece251116/export",
        method="post",
        q={"format": "json"},
    )
    dict_must_contain(
        res,
        required_keys=["state"],
        exception_dict_identifier="create export object",
    )
    processing_export = True
    while processing_export:
        res = req(
            f"api/study/b6f2c61b-d388-4412-8c9a-461ece251116/export/{res['export_id']}",
            method="get",
        )
        if res["state"] not in ["queued", "running"]:
            processing_export = False
        time.sleep(0.5)
    res = req(
        f"api/study/b6f2c61b-d388-4412-8c9a-461ece251116/export/{res['export_id']}/download",
        method="get",
    )
    print(res)


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
