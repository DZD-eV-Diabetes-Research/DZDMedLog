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
        study_name="TestListMultiInterviewsStudy",
        with_events=1,
        with_interviews_per_event_per_proband=1,
        proband_count=2,
    )

    study_id = study_data.study.id
    event = study_data.events[0]

    # List interviews
    interviews = req(
        f"api/study/{study_id}/event/{event.event.id}/interview",
        method="get",
    )
    print("interviews", interviews)
    from medlogserver.model.interview import Interview

    interview_attributes = list(Interview.model_fields.keys())
    assert len(interviews) == 2  # 2 probands * 1 interviews each
    for interview in interviews:
        dict_must_contain(
            interview,
            required_keys=interview_attributes,
            exception_dict_identifier="list interviews response item",
        )


def test_endpoint_study_event_multi_interview():
    """see https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues/127
    and https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues/130
    For now we only allow one interview per event per proband
    """
    from requests.exceptions import HTTPError

    try:
        study_data: TestDataContainerStudy = create_test_study(
            study_name="TestListInterviewsStudy",
            with_events=1,
            with_interviews_per_event_per_proband=2,
            proband_count=2,
        )
    except HTTPError as e:
        if e.response.status_code != 409:
            raise e
        # else all is fine. we expect the server to prevent us from creating more than one interview per event and probant.


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
        "proband_has_taken_meds": True,
    }

    from medlogserver.api.routes.routes_interview import create_interview

    new_interview = req(
        f"api/study/{study_id}/event/{event.event.id}/interview",
        method="post",
        b=interview_data,
    )
    from medlogserver.model.interview import Interview

    interview_attributes = list(Interview.model_fields.keys())

    dict_must_contain(
        new_interview,
        required_keys=interview_attributes,
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
    from medlogserver.model.interview import Interview

    interview_attributes = list(Interview.model_fields.keys())
    interview_details = req(
        f"api/study/{study_id}/event/{event.event.id}/interview/{interview.interview.id}",
        method="get",
    )

    dict_must_contain(
        interview_details,
        required_keys=interview_attributes,
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
    from medlogserver.model.interview import Interview

    interview_end_time = datetime.datetime.now().isoformat()

    update_data = {
        "interview_end_time_utc": interview_end_time,
    }

    updated_interview = req(
        f"api/study/{study_id}/event/{event.event.id}/interview/{interview.interview.id}",
        method="patch",
        b=update_data,
    )
    print("updated_interview", updated_interview)

    dict_must_contain(
        updated_interview,
        required_keys_and_val={"interview_end_time_utc": interview_end_time},
        exception_dict_identifier="update interview response",
    )
