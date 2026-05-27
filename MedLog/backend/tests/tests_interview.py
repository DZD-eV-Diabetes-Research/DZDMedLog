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
    create_test_user,
    authorize_for_access_token,
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


def test_endpoint_delete_interview_success():
    """Test DELETE /api/study/{study_id}/event/{event_id}/interview/{interview_id} - interview with no intakes"""
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestDeleteInterviewNoIntakesStudy",
        with_events=1,
        with_interviews_per_event_per_proband=1,
        proband_count=1,
        with_intakes=0,
    )
    study_id = study_data.study.id
    event = study_data.events[0]
    interview = event.interviews[0]

    req(
        f"api/study/{study_id}/event/{event.event.id}/interview/{interview.interview.id}",
        method="delete",
        expected_http_code=204,
    )

    # Verify the interview is gone
    remaining = req(
        f"api/study/{study_id}/event/{event.event.id}/interview",
        method="get",
    )
    interview_ids = [i["id"] for i in remaining]
    assert str(interview.interview.id) not in interview_ids


def test_endpoint_delete_interview_cascades_intakes():
    """Test DELETE interview also deletes all its intakes"""
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestDeleteInterviewCascadeStudy",
        with_events=1,
        with_interviews_per_event_per_proband=1,
        proband_count=1,
        with_intakes=2,
    )
    study_id = study_data.study.id
    event = study_data.events[0]
    interview = event.interviews[0]
    proband_id = study_data.proband_ids[0]

    # Verify intakes exist before deletion
    intakes_before = req(
        f"api/study/{study_id}/proband/{proband_id}/intake",
        method="get",
        q={"interview_id": str(interview.interview.id)},
    )
    assert intakes_before["count"] == 2

    req(
        f"api/study/{study_id}/event/{event.event.id}/interview/{interview.interview.id}",
        method="delete",
        expected_http_code=204,
    )

    # Verify intakes are gone after interview deletion
    intakes_after = req(
        f"api/study/{study_id}/proband/{proband_id}/intake",
        method="get",
        q={"interview_id": str(interview.interview.id)},
    )
    assert intakes_after["count"] == 0


def test_fix_for_issue_170():
    # https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues/170
    # "/study/{study_id}/proband/{proband_id}/interview"

    study1_data: TestDataContainerStudy = create_test_study(
        study_name="Test1_issue170",
        with_events=1,
        with_interviews_per_event_per_proband=1,
        proband_count=1,
    )
    # count inital interviews
    interview_list_study1 = req(
        f"api/study/{study1_data.study.id}/proband/{study1_data.proband_ids[0]}/interview",
        method="get",
    )
    assert len(interview_list_study1) == 1

    study2_data: TestDataContainerStudy = create_test_study(
        study_name="Test2_issue170",
        with_events=1,
        with_interviews_per_event_per_proband=1,
        proband_count=1,
    )
    # create interview in study 2 with same proband id from study 1

    interview_data_study2 = {
        "proband_external_id": study1_data.proband_ids[0],
        "interview_start_time_utc": datetime.datetime.now().isoformat(),
        "interview_end_time_utc": None,
        "interview_type": "regular",
        "interview_status": "in_progress",
        "proband_has_taken_meds": True,
    }

    from medlogserver.api.routes.routes_interview import create_interview

    new_interview = req(
        f"api/study/{study2_data.study.id}/event/{study2_data.events[0].event.id}/interview",
        method="post",
        b=interview_data_study2,
    )

    # list interviews from study1. we do not want to see any data from study2

    interview_list_study1 = req(
        f"api/study/{study1_data.study.id}/proband/{study1_data.proband_ids[0]}/interview",
        method="get",
    )
    print(f"count interview_list_study1: {len(interview_list_study1)}")
    assert len(interview_list_study1) == 1


def _create_interview_with_token(study_id, event_id, proband_id, access_token):
    """Helper: create an interview as a specific user and return the interview dict."""
    return req(
        f"api/study/{study_id}/event/{event_id}/interview",
        method="post",
        b={
            "proband_external_id": str(proband_id),
            "interview_start_time_utc": datetime.datetime.now().isoformat(),
            "interview_end_time_utc": None,
            "interview_type": "regular",
            "interview_status": "in_progress",
            "proband_has_taken_meds": True,
        },
        access_token=access_token,
    )


def _grant_study_permission(study_id, user_id, is_interviewer=False, is_admin=False):
    req(
        f"/api/study/{study_id}/permissions/{user_id}",
        method="put",
        b={"is_study_interviewer": is_interviewer, "is_study_admin": is_admin},
    )


def test_endpoint_delete_interview_non_owner_interviewer_is_blocked():
    """An interviewer who did NOT create the interview must be blocked (403)."""
    study_data = create_test_study(
        study_name="TestDeleteInterviewNonOwnerStudy",
        with_events=1,
        with_interviews_per_event_per_proband=0,
        proband_count=1,
    )
    study_id = study_data.study.id
    event = study_data.events[0]

    owner = create_test_user("interview_owner_A", "pw_owner_A", "owner_A@test.de")
    owner_token = authorize_for_access_token("interview_owner_A", "pw_owner_A")
    other = create_test_user("interview_other_B", "pw_other_B", "other_B@test.de")
    other_token = authorize_for_access_token("interview_other_B", "pw_other_B")

    _grant_study_permission(study_id, owner.id, is_interviewer=True)
    _grant_study_permission(study_id, other.id, is_interviewer=True)

    interview = _create_interview_with_token(
        study_id, event.event.id, study_data.proband_ids[0], owner_token
    )

    req(
        f"api/study/{study_id}/event/{event.event.id}/interview/{interview['id']}",
        method="delete",
        expected_http_code=403,
        access_token=other_token,
    )


def test_endpoint_delete_interview_owner_can_delete():
    """The interviewer who created the interview must be able to delete it."""
    study_data = create_test_study(
        study_name="TestDeleteInterviewOwnerStudy",
        with_events=1,
        with_interviews_per_event_per_proband=0,
        proband_count=1,
    )
    study_id = study_data.study.id
    event = study_data.events[0]

    owner = create_test_user("interview_owner_C", "pw_owner_C", "owner_C@test.de")
    owner_token = authorize_for_access_token("interview_owner_C", "pw_owner_C")
    _grant_study_permission(study_id, owner.id, is_interviewer=True)

    interview = _create_interview_with_token(
        study_id, event.event.id, study_data.proband_ids[0], owner_token
    )

    req(
        f"api/study/{study_id}/event/{event.event.id}/interview/{interview['id']}",
        method="delete",
        expected_http_code=204,
        access_token=owner_token,
    )


def test_endpoint_delete_interview_study_admin_can_delete_any():
    """A study admin must be able to delete any interview regardless of ownership."""
    study_data = create_test_study(
        study_name="TestDeleteInterviewStudyAdminStudy",
        with_events=1,
        with_interviews_per_event_per_proband=0,
        proband_count=1,
    )
    study_id = study_data.study.id
    event = study_data.events[0]

    owner = create_test_user("interview_owner_D", "pw_owner_D", "owner_D@test.de")
    owner_token = authorize_for_access_token("interview_owner_D", "pw_owner_D")
    study_admin = create_test_user(
        "interview_study_admin_E", "pw_sadmin_E", "sadmin_E@test.de"
    )
    study_admin_token = authorize_for_access_token(
        "interview_study_admin_E", "pw_sadmin_E"
    )

    _grant_study_permission(study_id, owner.id, is_interviewer=True)
    _grant_study_permission(study_id, study_admin.id, is_interviewer=True, is_admin=True)

    interview = _create_interview_with_token(
        study_id, event.event.id, study_data.proband_ids[0], owner_token
    )

    req(
        f"api/study/{study_id}/event/{event.event.id}/interview/{interview['id']}",
        method="delete",
        expected_http_code=204,
        access_token=study_admin_token,
    )
