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


def test_endpoint_study_list():
    """Test GET /api/study endpoint"""
    # Create multiple studies
    study1 = create_test_study(study_name="TestListStudy1", with_events=1)
    study2 = create_test_study(study_name="TestListStudy2", with_events=1)

    # List all studies
    response = req("api/study", method="get")

    dict_must_contain(
        response,
        required_keys=["total_count", "offset", "count", "items"],
        exception_dict_identifier="list studies response",
    )

    # Should contain at least our two test studies
    assert response["count"] >= 2

    # Verify study objects
    for study in response["items"]:
        dict_must_contain(
            study,
            required_keys=["id", "display_name", "created_at", "deactivated"],
            exception_dict_identifier="study item",
        )


def test_endpoint_study_create():
    """Test POST /api/study endpoint"""

    from medlogserver.model.study import StudyCreateAPI, Study
    from medlogserver.api.routes.routes_study import create_study

    study_name = "test_endpoint_study_create"
    study_data = StudyCreateAPI(display_name=study_name)
    study_response = req(
        "api/study",
        method="post",
        b=dictyfy(study_data),
    )
    print("study_response", study_response)

    dict_must_contain(
        study_response,
        required_keys=["id", "created_at"],
        required_keys_and_val={
            "deactivated": False,
            "display_name": study_name,
            "no_permissions": False,
        },
        exception_dict_identifier="create study response",
    )

    # Test duplicate study name
    req(
        "api/study",
        method="post",
        b=dictyfy(study_data),
        expected_http_code=409,
    )


def test_endpoint_study_update():
    """Test PATCH /api/study/{study_id} endpoint"""
    study_data = create_test_study(study_name="TestUpdateStudy", with_events=0)

    update_data = {
        "display_name": "Updated Study Name",
    }

    # Update study
    updated_study = req(
        f"api/study/{study_data.study.id}", method="patch", b=update_data
    )

    dict_must_contain(
        updated_study,
        required_keys=["id", "created_at"],
        required_keys_and_val={
            "deactivated": False,
            "display_name": "Updated Study Name",
            "no_permissions": False,
        },
        exception_dict_identifier="update study",
    )


def test_endpoint_study_delete():
    """Test DELETE /api/study/{study_id} endpoint"""
    study_data = create_test_study(study_name="TestDeleteStudy", with_events=0)

    # Try to delete study (should return 501 Not Implemented)
    req(
        f"api/study/{study_data.study.id}",
        method="delete",
        expected_http_code=501,
    )


def test_create_duplicate_study_name():
    from medlogserver.model.study import StudyCreateAPI, Study, StudyUpdate
    from medlogserver.api.routes.routes_study import create_study

    study_name = "test_create_duplicate_study_name"
    study_data = StudyCreateAPI(display_name=study_name)
    study_response = req(
        "api/study",
        method="post",
        b=dictyfy(study_data),
    )
    print("study_response", study_response)

    # Try duplicate study name
    req(
        "api/study",
        method="post",
        b=dictyfy(study_data),
        expected_http_code=409,
    )

    # create new study with temp
    new_study_with_temp_name = req(
        "api/study",
        method="post",
        b=dictyfy(StudyCreateAPI(display_name=f"{study_name}_tmp")),
    )

    # Try Update study with themp name to dupplicate name
    updated_study = req(
        f"api/study/{new_study_with_temp_name['id']}",
        method="patch",
        b=dictyfy(StudyUpdate(display_name=study_name)),
        expected_http_code=409,
    )


def test_endpoint_study_issue_190():
    """Test DELETE /api/study/{study_id}/permissions/{user_id} endpoint"""
    study_data = create_test_study(study_name="TestIssue190", with_events=1)

    # Create a test user ID (you would normally get this from a real user)
    test_user = create_test_user(
        user_name="user_test_endpoint_study_issue_190",
        password="we4r03rredf8",
        email="f@f2.de",
    )
    test_user_access_token = authorize_for_access_token(
        username=test_user.user_name,
        pw="we4r03rredf8",
        set_as_global_default_login=False,
    )

    study_list = req("api/study", method="get", access_token=test_user_access_token)
    dict_must_contain(
        study_list,
        required_keys_and_val={"total_count": 0, "offset": 0, "count": 0, "items": []},
        exception_dict_identifier="test_endpoint_study_issue_190",
    )


def test_endpoint_study_clone():
    """Test POST /api/study/{study_id}/clone endpoint (issue #330)

    A clone must carry over the complete study setup (proband ID config + event
    structure) but none of the collected data.
    """
    source = create_test_study(study_name="TestCloneSource", with_events=3)

    # give the source study a full proband-ID configuration, so we can verify that all
    # of it is carried over to the clone
    proband_id_config = {
        "proband_external_id_pattern": "^[A-Z]{3}[0-9]{4}$",
        "proband_external_id_pattern_error_text": "3 Großbuchstaben, dann 4 Ziffern",
        "proband_external_id_normalization": "uppercase",
        "proband_external_id_example": "AAA1111",
        "no_permissions": True,
    }
    req(f"api/study/{source.study.id}", method="patch", b=proband_id_config)

    clone = req(
        f"api/study/{source.study.id}/clone",
        method="post",
        b={"display_name": "TestCloneTarget"},
    )

    dict_must_contain(
        clone,
        required_keys=["id", "created_at"],
        required_keys_and_val={
            "display_name": "TestCloneTarget",
            "deactivated": False,
            **proband_id_config,
        },
        exception_dict_identifier="clone study response",
    )
    # a clone is a *new* study, not an alias of the source
    assert clone["id"] != str(source.study.id)

    # event structure is copied 1:1 (name + order_position), with fresh event ids
    source_events = req(f"api/study/{source.study.id}/event", method="get")["items"]
    clone_events = req(f"api/study/{clone['id']}/event", method="get")["items"]
    assert len(clone_events) == len(source_events) == 3
    assert [(e["name"], e["order_position"]) for e in clone_events] == [
        (e["name"], e["order_position"]) for e in source_events
    ]
    assert set(e["id"] for e in clone_events).isdisjoint(
        set(e["id"] for e in source_events)
    )
    for event in clone_events:
        assert event["study_id"] == clone["id"]


def test_endpoint_study_clone_does_not_copy_collected_data():
    """A clone starts empty: interviews/intakes of the source are not copied."""
    source = create_test_study(
        study_name="TestCloneNoData",
        with_events=2,
        with_interviews_per_event_per_proband=1,
        proband_count=2,
    )
    source_interviews = req(f"api/study/{source.study.id}/interview", method="get")
    assert len(source_interviews) > 0

    clone = req(
        f"api/study/{source.study.id}/clone",
        method="post",
        b={"display_name": "TestCloneNoDataTarget"},
    )
    clone_interviews = req(f"api/study/{clone['id']}/interview", method="get")
    assert clone_interviews == []


def test_endpoint_study_clone_duplicate_name():
    """Cloning to an already taken study name is rejected with 409."""
    source = create_test_study(study_name="TestCloneDuplicateSource", with_events=1)
    create_test_study(study_name="TestCloneDuplicateExisting", with_events=0)

    req(
        f"api/study/{source.study.id}/clone",
        method="post",
        b={"display_name": "TestCloneDuplicateExisting"},
        expected_http_code=409,
    )

    # the failed clone must not have left anything behind
    all_study_names = [
        s["display_name"] for s in req("api/study", method="get", q={"limit": 1000})["items"]
    ]
    assert all_study_names.count("TestCloneDuplicateExisting") == 1


def test_endpoint_study_clone_unknown_source():
    """Cloning a non existing study is rejected with 404."""
    req(
        f"api/study/{uuid.uuid4()}/clone",
        method="post",
        b={"display_name": "TestCloneUnknownSource"},
        expected_http_code=404,
    )


def test_endpoint_study_clone_empty_name():
    """An empty/whitespace only study name is rejected by validation."""
    source = create_test_study(study_name="TestCloneEmptyName", with_events=0)
    req(
        f"api/study/{source.study.id}/clone",
        method="post",
        b={"display_name": "   "},
        expected_http_code=422,
    )


def test_endpoint_study_clone_needs_admin():
    """Only instance admins may clone a study - same as creating one."""
    source = create_test_study(study_name="TestCloneNoAdmin", with_events=1)
    test_user = create_test_user(
        user_name="user_test_endpoint_study_clone",
        password="we4r03rredf8",
        email="clone_test_user@test.de",
    )
    test_user_access_token = authorize_for_access_token(
        username=test_user.user_name,
        pw="we4r03rredf8",
        set_as_global_default_login=False,
    )
    req(
        f"api/study/{source.study.id}/clone",
        method="post",
        b={"display_name": "TestCloneNoAdminTarget"},
        access_token=test_user_access_token,
        expected_http_code=403,
    )


def test_endpoint_study_clone_deactivated_source():
    """A deactivated study stays usable as a template - the clone is created active."""
    source = create_test_study(study_name="TestCloneDeactivated", with_events=2)
    req(
        f"api/study/{source.study.id}",
        method="patch",
        b={"deactivated": True},
    )

    clone = req(
        f"api/study/{source.study.id}/clone",
        method="post",
        b={"display_name": "TestCloneDeactivatedTarget"},
    )
    assert clone["deactivated"] is False
    clone_events = req(f"api/study/{clone['id']}/event", method="get")["items"]
    assert len(clone_events) == 2
