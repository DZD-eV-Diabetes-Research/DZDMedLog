from typing import List, Dict
import json
import datetime
from _single_test_file_runner import run_all_tests_if_test_file_called

if __name__ == "__main__":
    run_all_tests_if_test_file_called()

from utils import (
    req,
    dict_must_contain,
    create_test_study,
    TestDataContainerStudy,
)


def test_endpoint_study_event_interview_list():
    """Test GET /api/study/{study_id}/event/{event_id}/interview endpoint"""
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestListInterviewsStudy",
        with_events=1,
        with_interviews_per_event_per_proband=2,
        proband_count=2,
    )

    study_id = study_data.study.id
    event = study_data.events[0]

    # List interviews
    interviews = req(
        f"api/study/{study_id}/event/{event.event.id}/interview", method="get"
    )

    assert len(interviews) == 4  # 2 probands * 2 interviews each
    for interview in interviews:
        dict_must_contain(
            interview,
            required_keys=[
                "id",
                "proband_external_id",
                "interview_start_time_utc",
                "interview_type",
                "interview_status",
            ],
            exception_dict_identifier="list interviews response item",
        )


def test_endpoint_study_event_interview_create():
    """Test POST /api/study/{study_id}/event/{event_id}/interview endpoint"""
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestCreateInterviewStudy",
        with_events=1,
        with_interviews_per_event_per_proband=0,
        proband_count=1,
    )

    study_id = study_data.study.id
    event = study_data.events[0]
    proband_id = study_data.proband_ids[0]

    interview_data = {
        "proband_external_id": proband_id,
        "interview_start_time_utc": datetime.datetime.now().isoformat(),
        "interview_end_time_utc": None,
        "interview_type": "regular",
        "interview_status": "in_progress",
    }

    new_interview = req(
        f"api/study/{study_id}/event/{event.event.id}/interview",
        method="post",
        b=interview_data,
    )

    dict_must_contain(
        new_interview,
        required_keys=[
            "id",
            "proband_external_id",
            "interview_start_time_utc",
            "interview_type",
            "interview_status",
        ],
        exception_dict_identifier="create interview response",
    )


def test_endpoint_study_event_interview_get():
    """Test GET /api/study/{study_id}/event/{event_id}/interview/{interview_id} endpoint"""
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestGetInterviewStudy",
        with_events=1,
        with_interviews_per_event_per_proband=1,
        proband_count=1,
    )

    study_id = study_data.study.id
    event = study_data.events[0]
    interview = event.interviews[0]

    interview_details = req(
        f"api/study/{study_id}/event/{event.event.id}/interview/{interview.interview.id}",
        method="get",
    )

    dict_must_contain(
        interview_details,
        required_keys=[
            "id",
            "proband_external_id",
            "interview_start_time_utc",
            "interview_type",
            "interview_status",
        ],
        exception_dict_identifier="get interview response",
    )


def test_endpoint_study_event_interview_update():
    """Test PATCH /api/study/{study_id}/event/{event_id}/interview/{interview_id} endpoint"""
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestUpdateInterviewStudy",
        with_events=1,
        with_interviews_per_event_per_proband=1,
        proband_count=1,
    )

    study_id = study_data.study.id
    event = study_data.events[0]
    interview = event.interviews[0]

    update_data = {
        "interview_end_time_utc": datetime.datetime.now().isoformat(),
        "interview_status": "completed",
    }

    updated_interview = req(
        f"api/study/{study_id}/event/{event.event.id}/interview/{interview.interview.id}",
        method="patch",
        b=update_data,
    )

    dict_must_contain(
        updated_interview,
        required_keys_and_val={"interview_status": "completed"},
        required_keys=["interview_end_time_utc"],
        exception_dict_identifier="update interview response",
    )
