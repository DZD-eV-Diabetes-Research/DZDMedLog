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
        with_events=3,
        with_interviews_per_event_per_proband=3,
        with_intakes=3,
    )
    print("study_data::", study_data)
