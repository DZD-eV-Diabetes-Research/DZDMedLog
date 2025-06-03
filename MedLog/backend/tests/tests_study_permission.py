from typing import List, Dict
import json
import uuid
from _single_test_file_runner import run_all_tests_if_test_file_called

if __name__ == "__main__":
    run_all_tests_if_test_file_called()

from utils import (
    req,
    dict_must_contain,
    create_test_study,
    TestDataContainerStudy,
    create_test_user,
    authorize,
    dictyfy,
)


def test_endpoint_study_permissions_list():
    """Test GET /api/study/{study_id}/permissions endpoint"""
    study_data = create_test_study(study_name="TestListPermissionsStudy", with_events=0)

    # List permissions
    response = req(f"api/study/{study_data.study.id}/permissions", method="get")

    dict_must_contain(
        response,
        required_keys=["total_count", "offset", "count", "items"],
        exception_dict_identifier="list permissions response",
    )

    # Verify permission objects
    for permission in response["items"]:
        dict_must_contain(
            permission,
            required_keys=[
                "id",
                "user_id",
                "study_id",
                "is_study_admin",
                "is_interviewer",
                "created_at",
            ],
            exception_dict_identifier="permission item",
        )


def test_endpoint_study_permissions_get():
    """Test GET /api/study/{study_id}/permissions/{permission_id} endpoint"""
    study_data = create_test_study(study_name="TestGetPermissionStudy", with_events=3)
    user_password = "we9gij2409rv"
    test_user = create_test_user(
        user_name="permtestuser", password=user_password, email="ptest@test.com"
    )
    test_user_access_token = authorize(
        username=test_user.user_name,
        pw=user_password,
        set_as_global_default_login=False,
    )

    from medlogserver.api.routes.routes_event import list_events

    # Step1 new test user should not see the study as the account has not permission

    res = req(
        f"/api/study/{study_data.study.id}/event",
        method="get",
        access_token=test_user_access_token,
        tolerated_error_codes=[404],
    )
    assert "does not exist" in res["detail"]
    print("res", res)

    # Step 2: create persmission with admin
    from medlogserver.api.routes.routes_study_permission import (
        create_or_update_permission,
    )
    from medlogserver.model.study_permission import StudyPermissonUpdate

    view_perm = StudyPermissonUpdate(is_study_viewer=1)
    result_permission = req(
        f"/api/study/{study_data.study.id}/permissions/{test_user.id}",
        method="put",
        b=dictyfy(view_perm),
    )
    print("result_permission", result_permission)
    assert {
        "is_study_interviewer": False,
        "is_study_admin": False,
        "is_study_viewer": True,
    } == result_permission

    events = req(
        f"/api/study/{study_data.study.id}/event",
        method="get",
        access_token=test_user_access_token,
    )
    print("events", events)

    assert len(events["items"]) == 3
    # step 3: we still should not be allowed to create an interview
    from medlogserver.model.interview import InterviewCreateAPI

    interview_create = InterviewCreateAPI(
        proband_external_id="4356", proband_has_taken_meds=True
    )
    res = req(
        f"/api/study/{study_data.study.id}/event/{study_data.events[0].event.id}/interview",
        method="post",
        b=dictyfy(interview_create),
        access_token=test_user_access_token,
        tolerated_error_codes=[401],
    )
    assert res == {"detail": "User not authorized to create interview in this study"}

    # step 4: give inetrview permissions
    view_perm = StudyPermissonUpdate(is_study_interviewer=1)
    result_permission = req(
        f"/api/study/{study_data.study.id}/permissions/{test_user.id}",
        method="put",
        b=dictyfy(view_perm),
    )
    assert {
        "is_study_interviewer": True,
        "is_study_admin": False,
        "is_study_viewer": True,
    } == result_permission


def test_endpoint_study_permissions_create_or_update():
    """Test PUT /api/study/{study_id}/permissions/{user_id} endpoint"""
    study_data = create_test_study(
        study_name="TestCreatePermissionStudy", with_events=0
    )

    # Create a test user ID (you would normally get this from a real user)
    test_user_id = str(uuid.uuid4())

    # Create permission data
    permission_data = {"is_study_admin": True, "is_interviewer": True}

    # Create new permission
    new_permission = req(
        f"api/study/{study_data.study.id}/permissions/{test_user_id}",
        method="put",
        b=permission_data,
    )

    dict_must_contain(
        new_permission,
        required_keys=[
            "id",
            "user_id",
            "study_id",
            "is_study_admin",
            "is_interviewer",
            "created_at",
        ],
        required_keys_and_val={
            "is_study_admin": permission_data["is_study_admin"],
            "is_interviewer": permission_data["is_interviewer"],
            "user_id": test_user_id,
            "study_id": str(study_data.study.id),
        },
        exception_dict_identifier="create permission response",
    )

    # Update permission
    update_data = {"is_study_admin": False, "is_interviewer": True}

    # Update existing permission
    updated_permission = req(
        f"api/study/{study_data.study.id}/permissions/{test_user_id}",
        method="put",
        b=update_data,
    )

    dict_must_contain(
        updated_permission,
        required_keys=[
            "id",
            "user_id",
            "study_id",
            "is_study_admin",
            "is_interviewer",
            "created_at",
        ],
        required_keys_and_val={
            "is_study_admin": update_data["is_study_admin"],
            "is_interviewer": update_data["is_interviewer"],
            "user_id": test_user_id,
            "study_id": str(study_data.study.id),
        },
        exception_dict_identifier="update permission response",
    )


def test_full_permission_workflow():
    """Test GET /api/study/{study_id}/permissions/{permission_id} endpoint"""
    study_data = create_test_study(study_name="TestGetPermissionStudy", with_events=3)
    user_password = "we9gij2409rv"
    test_user = create_test_user(
        user_name="permtestuser", password=user_password, email="ptest@test.com"
    )
    test_user_access_token = authorize(
        username=test_user.user_name,
        pw=user_password,
        set_as_global_default_login=False,
    )

    from medlogserver.api.routes.routes_event import list_events

    # Step1 new test user should not see the study as the account has not permission

    res = req(
        f"/api/study/{study_data.study.id}/event",
        method="get",
        access_token=test_user_access_token,
        tolerated_error_codes=[404],
    )
    assert "does not exist" in res["detail"]
    print("res", res)

    # Step 2: create persmission with admin
    from medlogserver.api.routes.routes_study_permission import (
        create_or_update_permission,
    )
    from medlogserver.model.study_permission import StudyPermissonUpdate

    view_perm = StudyPermissonUpdate(is_study_viewer=1)
    result_permission = req(
        f"/api/study/{study_data.study.id}/permissions/{test_user.id}",
        method="put",
        b=dictyfy(view_perm),
    )
    print("result_permission", result_permission)
    assert {
        "is_study_interviewer": False,
        "is_study_admin": False,
        "is_study_viewer": True,
    } == result_permission

    events = req(
        f"/api/study/{study_data.study.id}/event",
        method="get",
        access_token=test_user_access_token,
    )
    print("events", events)

    assert len(events["items"]) == 3
    # step 3: we still should not be allowed to create an interview
    from medlogserver.model.interview import InterviewCreateAPI

    interview_create = InterviewCreateAPI(
        proband_external_id="4356", proband_has_taken_meds=True
    )
    res = req(
        f"/api/study/{study_data.study.id}/event/{study_data.events[0].event.id}/interview",
        method="post",
        b=dictyfy(interview_create),
        access_token=test_user_access_token,
        tolerated_error_codes=[401],
    )
    assert res == {"detail": "User not authorized to create interview in this study"}

    # step 4: give inetrview permissions
    view_perm = StudyPermissonUpdate(is_study_interviewer=1)
    result_permission = req(
        f"/api/study/{study_data.study.id}/permissions/{test_user.id}",
        method="put",
        b=dictyfy(view_perm),
    )
    assert {
        "is_study_interviewer": True,
        "is_study_admin": False,
        "is_study_viewer": True,
    } == result_permission

    from medlogserver.api.routes.routes_interview import create_interview

    created_interview = req(
        f"/api/study/{study_data.study.id}/event/{study_data.events[0].event.id}/interview",
        method="post",
        b=dictyfy(interview_create),
        access_token=test_user_access_token,
    )
    print("created_interview", created_interview)
    dict_must_contain(
        created_interview,
        required_keys=["interview_start_time_utc"],
        required_keys_and_val={"proband_external_id": "4356"},
    )

    # step 5: user is still not allowed to create a new event
    from medlogserver.model.event import EventCreateAPI, EventRead
    from medlogserver.api.routes.routes_event import create_event

    event = EventCreateAPI(name=f"EventTestPerm", order_position=99)

    res = req(
        f"api/study/{study_data.study.id}/event",
        method="post",
        b=dictyfy(event),
        access_token=test_user_access_token,
        tolerated_error_codes=[401],
    )
    print("res", res)
    assert res == {"detail": "Not authorized to create new event"}

    # step 6: Give user study adminrights
    view_perm = StudyPermissonUpdate(is_study_admin=1)
    result_permission = req(
        f"/api/study/{study_data.study.id}/permissions/{test_user.id}",
        method="put",
        b=dictyfy(view_perm),
    )
    print("result_permission", result_permission)
    assert {
        "is_study_interviewer": True,
        "is_study_admin": True,
        "is_study_viewer": True,
    } == result_permission
    res = req(
        f"api/study/{study_data.study.id}/event",
        method="post",
        b=dictyfy(event),
        access_token=test_user_access_token,
    )
    print("res", res)
    events = req(
        f"/api/study/{study_data.study.id}/event",
        method="get",
        access_token=test_user_access_token,
    )
    print("events", events)

    # we now should have 4 events
    assert len(events["items"]) == 4
