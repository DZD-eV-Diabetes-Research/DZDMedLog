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
    study_data = {
        "display_name": "Test Study Creation",
        "description": "A test study for testing study creation",
    }

    # Create new study
    new_study = req("api/study", method="post", b=study_data)

    dict_must_contain(
        new_study,
        required_keys=["id", "display_name", "created_at", "deactivated"],
        required_keys_and_val={
            "display_name": study_data["display_name"],
            "description": study_data["description"],
            "deactivated": False,
        },
        exception_dict_identifier="create study response",
    )

    # Test duplicate study name
    req(
        "api/study",
        method="post",
        b=study_data,
        expected_http_code=400,
        tolerated_error_codes=[400],
    )


def test_endpoint_study_update():
    """Test PATCH /api/study/{study_id} endpoint"""
    study_data = create_test_study(study_name="TestUpdateStudy", with_events=0)

    update_data = {
        "display_name": "Updated Study Name",
        "description": "Updated study description",
    }

    # Update study
    updated_study = req(
        f"api/study/{study_data.study.id}", method="patch", b=update_data
    )

    dict_must_contain(
        updated_study,
        required_keys=["id", "display_name", "created_at", "deactivated"],
        required_keys_and_val={
            "display_name": update_data["display_name"],
            "description": update_data["description"],
        },
        exception_dict_identifier="update study response",
    )


def test_endpoint_study_delete():
    """Test DELETE /api/study/{study_id} endpoint"""
    study_data = create_test_study(study_name="TestDeleteStudy", with_events=0)

    # Try to delete study (should return 501 Not Implemented)
    req(
        f"api/study/{study_data.study.id}",
        method="delete",
        expected_http_code=501,
        tolerated_error_codes=[501],
    )
