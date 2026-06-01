from typing import List, Dict
import json
import datetime
import uuid

from utils import (
    req,
    dict_must_contain,
    create_test_study,
    TestDataContainerStudy,
    create_test_user,
    authorize_for_access_token,
)


def test_endpoint_study_event_list():
    """Test GET /api/study/{study_id}/event endpoint"""
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestListEventsStudy",
        with_events=3,
        with_interviews_per_event_per_proband=1,
        proband_count=1,
    )

    # List all events
    response = req(f"api/study/{study_data.study.id}/event", method="get")

    dict_must_contain(
        response,
        required_keys=["total_count", "offset", "count", "items"],
        exception_dict_identifier="list events response",
    )

    assert response["count"] == 3
    for event in response["items"]:
        dict_must_contain(
            event,
            required_keys=["id", "name", "order_position", "study_id"],
            exception_dict_identifier="event item",
        )


def test_endpoint_study_event_create():
    """Test POST /api/study/{study_id}/event endpoint"""
    from medlogserver.model.event import Event, EventCreateAPI
    from medlogserver.api.routes.routes_event import create_event

    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestCreateEventStudy", with_events=0
    )

    # Create new event
    event_data = {
        "name": "Test Event",
        "order_position": 10,
    }

    new_event = req(
        f"api/study/{study_data.study.id}/event", method="post", b=event_data
    )

    dict_must_contain(
        new_event,
        required_keys=["id", "name", "order_position", "study_id"],
        required_keys_and_val={
            "name": event_data["name"],
            "order_position": event_data["order_position"],
        },
        exception_dict_identifier="create event response",
    )


def test_endpoint_study_event_update():
    """Test PATCH /api/study/{study_id}/event/{event_id} endpoint"""
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestUpdateEventStudy", with_events=1
    )

    event = study_data.events[0]

    # Update event
    update_data = {
        "name": "Updated Event Name",
        "description": "Updated event description",
    }

    updated_event = req(
        f"api/study/{study_data.study.id}/event/{event.event.id}",
        method="patch",
        b=update_data,
    )

    dict_must_contain(
        updated_event,
        required_keys=["id", "name", "order_position", "study_id"],
        required_keys_and_val={
            "name": update_data["name"],
        },
        exception_dict_identifier="update event response",
    )


def test_endpoint_delete_event_success():
    """Test DELETE /api/study/{study_id}/event/{event_id} - empty event can be deleted"""
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestDeleteEventSuccessStudy",
        with_events=1,
        with_interviews_per_event_per_proband=0,
    )
    event = study_data.events[0]

    req(
        f"api/study/{study_data.study.id}/event/{event.event.id}",
        method="delete",
        expected_http_code=204,
    )

    # Verify the event is gone
    remaining = req(f"api/study/{study_data.study.id}/event", method="get")
    event_ids = [e["id"] for e in remaining["items"]]
    assert str(event.event.id) not in event_ids


def test_endpoint_delete_event_blocked_by_interviews():
    """Test DELETE /api/study/{study_id}/event/{event_id} - event with interviews returns 409"""
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestDeleteEventBlockedStudy",
        with_events=1,
        with_interviews_per_event_per_proband=1,
        proband_count=1,
    )
    event = study_data.events[0]
    interview = event.interviews[0]

    response = req(
        f"api/study/{study_data.study.id}/event/{event.event.id}",
        method="delete",
        expected_http_code=409,
    )

    assert response["detail"]["error"] == "event not empty"
    assert str(interview.interview.id) in response["detail"]["following interviews, interview_ids"]


def test_endpoint_study_event_order_create():
    """Test POST /api/study/{study_id}/event/order endpoint"""
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestReorderEventsStudy", with_events=3
    )

    events = study_data.events
    event_ids = [str(event.event.id) for event in events]

    # Reorder events
    from medlogserver.api.routes.routes_event import reorder_events

    reordered_events = req(
        f"api/study/{study_data.study.id}/event/order", method="post", b=event_ids
    )

    assert len(reordered_events) == 3
    for i, event in enumerate(reordered_events):
        dict_must_contain(
            event,
            required_keys=["id", "name", "order_position", "study_id"],
            exception_dict_identifier=f"reordered event {i}",
        )


def test_endpoint_study_proband_event_list():
    """Test GET /api/study/{study_id}/proband/{proband_id}/event endpoint"""
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestListProbandEventsStudy",
        with_events=2,
        with_interviews_per_event_per_proband=1,
        proband_count=1,
    )

    proband_id = study_data.proband_ids[0]

    # List events for proband
    response = req(
        f"api/study/{study_data.study.id}/proband/{proband_id}/event", method="get"
    )

    dict_must_contain(
        response,
        required_keys=["total_count", "offset", "count", "items"],
        exception_dict_identifier="list proband events response",
    )

    assert response["count"] == 2
    for event in response["items"]:
        dict_must_contain(
            event,
            required_keys=[
                "id",
                "name",
                "order_position",
                "study_id",
                "proband_interview_count",
            ],
            exception_dict_identifier="proband event item",
        )
        assert event["proband_interview_count"] == 1  # We created 1 interview per event


def test_endpoint_delete_event_interviewer_is_blocked():
    """Interviewers (non-admin) must not be able to delete events — requires study_admin."""
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestDeleteEventInterviewerBlockedStudy",
        with_events=1,
        with_interviews_per_event_per_proband=0,
    )
    event = study_data.events[0]

    interviewer = create_test_user(
        user_name="interviewer_delete_event_blocked",
        password="pw_interviewer_del_evt",
        email="interviewer_del_evt@test.de",
    )
    interviewer_token = authorize_for_access_token(
        username="interviewer_delete_event_blocked", pw="pw_interviewer_del_evt"
    )
    req(
        f"/api/study/{study_data.study.id}/permissions/{interviewer.id}",
        method="put",
        b={"is_study_interviewer": True, "is_study_admin": False},
    )

    req(
        f"api/study/{study_data.study.id}/event/{event.event.id}",
        method="delete",
        expected_http_code=403,
        access_token=interviewer_token,
    )


def test_endpoint_delete_event_study_admin_can_delete():
    """Study admin (and global admin) must be able to delete an empty event."""
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TestDeleteEventStudyAdminStudy",
        with_events=1,
        with_interviews_per_event_per_proband=0,
    )
    event = study_data.events[0]

    study_admin = create_test_user(
        user_name="study_admin_delete_event",
        password="pw_study_admin_del_evt",
        email="study_admin_del_evt@test.de",
    )
    study_admin_token = authorize_for_access_token(
        username="study_admin_delete_event", pw="pw_study_admin_del_evt"
    )
    req(
        f"/api/study/{study_data.study.id}/permissions/{study_admin.id}",
        method="put",
        b={"is_study_interviewer": True, "is_study_admin": True},
    )

    req(
        f"api/study/{study_data.study.id}/event/{event.event.id}",
        method="delete",
        expected_http_code=204,
        access_token=study_admin_token,
    )
