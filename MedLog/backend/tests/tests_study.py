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
