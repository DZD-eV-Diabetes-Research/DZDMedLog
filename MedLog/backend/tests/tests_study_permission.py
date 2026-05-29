from typing import List, Dict
import json
import uuid

from utils import (
    req,
    dict_must_contain,
    create_test_study,
    TestDataContainerStudy,
    create_test_user,
    authorize_for_access_token,
    dictyfy,
)
from statics import ADMIN_USER_NAME, ADMIN_USER_PW


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
    """Test GET /api/study/{study_id}/permissions/{user_id} endpoint"""
    study_data = create_test_study(study_name="TestGetPermissionStudy", with_events=3)
    user_password = "we9gij2409rv"
    test_user = create_test_user(
        user_name="permtestuser", password=user_password, email="ptest@test.com"
    )
    test_user_access_token = authorize_for_access_token(
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
    dict_must_contain(
        d=result_permission,
        required_keys_and_val={
            "is_study_interviewer": False,
            "is_study_admin": False,
            "is_study_viewer": True,
        },
    )
    permission_get = req(
        f"/api/study/{study_data.study.id}/permissions/{test_user.id}",
        method="get",
    )
    print("result_permission", result_permission)
    print("permission_get", permission_get)

    assert result_permission == permission_get

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
    dict_must_contain(
        d=result_permission,
        required_keys_and_val={
            "is_study_interviewer": True,
            "is_study_admin": False,
            "is_study_viewer": True,
        },
    )


def test_endpoint_study_permissions_create_or_update():
    """Test PUT /api/study/{study_id}/permissions/{user_id} endpoint"""
    study_data = create_test_study(
        study_name="TestCreatePermissionStudy", with_events=0
    )

    # Create a test user ID (you would normally get this from a real user)
    test_user_id = create_test_user(
        user_name="user_test_endpoint_study_permissions_create_or_update",
        password="we4r03rredf8",
        email="f@f.de",
    )

    # Create permission data
    permission_data = {"is_study_admin": True, "is_study_interviewer": True}

    # Create new permission
    new_permission = req(
        f"api/study/{study_data.study.id}/permissions/{test_user_id.id}",
        method="put",
        b=permission_data,
    )

    dict_must_contain(
        new_permission,
        required_keys_and_val={"is_study_admin": True, "is_study_interviewer": True},
        exception_dict_identifier="create permission response",
    )

    # Update permission
    update_data = {"is_study_admin": False, "is_study_interviewer": True}

    # Update existing permission
    updated_permission = req(
        f"api/study/{study_data.study.id}/permissions/{test_user_id.id}",
        method="put",
        b=update_data,
    )

    dict_must_contain(
        updated_permission,
        required_keys_and_val={"is_study_admin": False, "is_study_interviewer": True},
        exception_dict_identifier="create permission response",
    )


def test_endpoint_study_permissions_delete():
    """Test DELETE /api/study/{study_id}/permissions/{user_id} endpoint"""
    study_data = create_test_study(
        study_name="TestDeletePermissionStudy", with_events=1
    )

    # Create a test user ID (you would normally get this from a real user)
    test_user = create_test_user(
        user_name="user_test_endpoint_study_permissions_delete",
        password="we4r03rredf8",
        email="f@f2.de",
    )
    test_user_access_token = authorize_for_access_token(
        username=test_user.user_name,
        pw="we4r03rredf8",
        set_as_global_default_login=False,
    )

    # Create permission data
    permission_data = {"is_study_admin": True, "is_study_interviewer": True}

    # Create new permission
    new_permission = req(
        f"api/study/{study_data.study.id}/permissions/{test_user.id}",
        method="put",
        b=permission_data,
    )

    dict_must_contain(
        new_permission,
        required_keys_and_val={"is_study_admin": True, "is_study_interviewer": True},
        exception_dict_identifier="create permission response",
    )

    events = req(
        f"/api/study/{study_data.study.id}/event",
        method="get",
        access_token=test_user_access_token,
    )
    # user is now alloweed to see events
    print("events", events)
    assert len(events["items"]) == 1

    # Delete existing permission
    delete_response = req(
        f"api/study/{study_data.study.id}/permissions/{test_user.id}",
        method="delete",
        expected_http_code=204,
    )

    # Test if permission is not existent now
    req(
        f"api/study/{study_data.study.id}/permissions/{test_user.id}",
        method="get",
        expected_http_code=404,
    )
    # user should now not see the study at all
    events = req(
        f"/api/study/{study_data.study.id}/event",
        method="get",
        access_token=test_user_access_token,
        expected_http_code=404,
    )


def test_full_permission_workflow():

    study_data = create_test_study(
        study_name="TestStudyPermissionFullWorkflow", with_events=3
    )
    user_password = "we9gij2409rv"
    test_user = create_test_user(
        user_name="user_test_full_permission_workflow",
        password=user_password,
        email="pwftest@test.com",
    )
    test_user_access_token = authorize_for_access_token(
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
    dict_must_contain(
        result_permission,
        required_keys_and_val={
            "is_study_interviewer": False,
            "is_study_admin": False,
            "is_study_viewer": True,
        },
        exception_dict_identifier="create permission response",
    )

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
    dict_must_contain(
        result_permission,
        required_keys_and_val={
            "is_study_interviewer": True,
            "is_study_admin": False,
            "is_study_viewer": True,
        },
        exception_dict_identifier="create permission response",
    )

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
    dict_must_contain(
        result_permission,
        required_keys_and_val={
            "is_study_interviewer": True,
            "is_study_admin": True,
            "is_study_viewer": True,
        },
        exception_dict_identifier="create permission response",
    )

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


def test_endpoint_study_permissions_me_as_admin_without_db_row():
    """Admin user with no explicit DB permission row must get a synthetic all-true permission."""
    study_data = create_test_study(
        study_name="TestAdminPermsMeNoDBRow", with_events=0
    )
    # The default req() uses the admin token; admin has no DB row for this fresh study.
    result = req(
        f"/api/study/{study_data.study.id}/permissions/me",
        method="get",
    )
    dict_must_contain(
        result,
        required_keys_and_val={
            "is_study_viewer": True,
            "is_study_interviewer": True,
            "is_study_admin": True,
        },
        exception_dict_identifier="admin synthetic permission",
    )
    assert result["user_id"] is not None
    assert result["study_id"] == str(study_data.study.id)


def test_endpoint_study_permissions_me_as_admin_with_explicit_db_row():
    """Admin user who also has an explicit DB permission row should still get a valid response."""
    study_data = create_test_study(
        study_name="TestAdminPermsMeWithDBRow", with_events=0
    )
    # Fetch admin user info via /user/me
    admin_info = req("/api/user/me", method="get")
    admin_id = admin_info["id"]

    # Create an explicit (but restricted) DB permission for the admin
    from medlogserver.model.study_permission import StudyPermissonUpdate

    restricted_perm = StudyPermissonUpdate(
        is_study_viewer=True, is_study_interviewer=False, is_study_admin=False
    )
    req(
        f"/api/study/{study_data.study.id}/permissions/{admin_id}",
        method="put",
        b=dictyfy(restricted_perm),
    )

    # /permissions/me should return the DB row, not the synthetic all-true one
    result = req(
        f"/api/study/{study_data.study.id}/permissions/me",
        method="get",
    )
    dict_must_contain(
        result,
        required_keys_and_val={
            "is_study_viewer": True,
            "is_study_interviewer": False,
            "is_study_admin": False,
        },
        exception_dict_identifier="admin explicit permission",
    )
    assert result["user_id"] == admin_id


def test_endpoint_study_permissions_me_as_regular_user():
    """Regular user with an explicit study permission gets their actual permission record."""
    study_data = create_test_study(
        study_name="TestRegularUserPermsMe", with_events=0
    )
    user_password = "reguser_pw_9301"
    test_user = create_test_user(
        user_name="perms_me_regular_user",
        password=user_password,
        email="perms_me_regular@test.com",
    )
    test_user_token = authorize_for_access_token(
        username=test_user.user_name,
        pw=user_password,
        set_as_global_default_login=False,
    )

    from medlogserver.model.study_permission import StudyPermissonUpdate

    # Grant viewer + interviewer, not admin
    perm = StudyPermissonUpdate(
        is_study_viewer=True, is_study_interviewer=True, is_study_admin=False
    )
    req(
        f"/api/study/{study_data.study.id}/permissions/{test_user.id}",
        method="put",
        b=dictyfy(perm),
    )

    result = req(
        f"/api/study/{study_data.study.id}/permissions/me",
        method="get",
        access_token=test_user_token,
    )
    dict_must_contain(
        result,
        required_keys_and_val={
            "is_study_viewer": True,
            "is_study_interviewer": True,
            "is_study_admin": False,
        },
        exception_dict_identifier="regular user permission /me",
    )
    assert result["user_id"] == str(test_user.id)


def test_endpoint_study_permissions_me_as_usermanager_without_db_row():
    """Usermanager with no explicit DB permission row gets a synthetic viewer-only permission."""
    from medlogserver.config import Config as _Config

    _config = _Config()
    study_data = create_test_study(
        study_name="TestUsermanagerPermsMeNoDBRow", with_events=0
    )
    user_password = "umgr_pw_4821"
    um_user = create_test_user(
        user_name="perms_me_usermanager",
        password=user_password,
        email="perms_me_usermanager@test.com",
    )
    # Elevate to usermanager role (no admin)
    req(
        f"/api/user/{um_user.id}",
        method="patch",
        b={"roles": [_config.USERMANAGER_ROLE_NAME]},
    )
    um_token = authorize_for_access_token(
        username=um_user.user_name,
        pw=user_password,
        set_as_global_default_login=False,
    )

    result = req(
        f"/api/study/{study_data.study.id}/permissions/me",
        method="get",
        access_token=um_token,
    )
    # Usermanagers get implicit viewer access only — no interviewer or study-admin rights
    dict_must_contain(
        result,
        required_keys_and_val={
            "is_study_viewer": True,
            "is_study_interviewer": False,
            "is_study_admin": False,
        },
        exception_dict_identifier="usermanager synthetic permission",
    )
    assert result["user_id"] == str(um_user.id)
    assert result["study_id"] == str(study_data.study.id)


def test_endpoint_study_permissions_me_as_usermanager_with_explicit_db_row():
    """Usermanager who also has an explicit DB permission row gets that row back."""
    from medlogserver.config import Config as _Config
    from medlogserver.model.study_permission import StudyPermissonUpdate

    _config = _Config()
    study_data = create_test_study(
        study_name="TestUsermanagerPermsMeWithDBRow", with_events=0
    )
    user_password = "umgr_pw_2954"
    um_user = create_test_user(
        user_name="perms_me_usermanager_dbrow",
        password=user_password,
        email="perms_me_usermanager_dbrow@test.com",
    )
    req(
        f"/api/user/{um_user.id}",
        method="patch",
        b={"roles": [_config.USERMANAGER_ROLE_NAME]},
    )
    um_token = authorize_for_access_token(
        username=um_user.user_name,
        pw=user_password,
        set_as_global_default_login=False,
    )

    # Give an explicit interviewer permission via admin
    explicit_perm = StudyPermissonUpdate(is_study_interviewer=True)
    req(
        f"/api/study/{study_data.study.id}/permissions/{um_user.id}",
        method="put",
        b=dictyfy(explicit_perm),
    )

    result = req(
        f"/api/study/{study_data.study.id}/permissions/me",
        method="get",
        access_token=um_token,
    )
    # Should return the DB row, not the synthetic viewer-only one
    dict_must_contain(
        result,
        required_keys_and_val={
            "is_study_viewer": True,
            "is_study_interviewer": True,
        },
        exception_dict_identifier="usermanager explicit permission",
    )
    assert result["user_id"] == str(um_user.id)


def test_endpoint_study_permissions_delete_nonexistent_returns_404():
    """Deleting a permission that does not exist must return 404, not crash."""
    study_data = create_test_study(
        study_name="TestDeleteNonexistentPermission", with_events=0
    )
    # Create a user but give them no study permission
    no_perm_user = create_test_user(
        user_name="delete_perm_no_perm_user",
        password="delperm_pw_7731",
        email="delete_perm_noperm@test.com",
    )
    req(
        f"/api/study/{study_data.study.id}/permissions/{no_perm_user.id}",
        method="delete",
        expected_http_code=404,
    )
