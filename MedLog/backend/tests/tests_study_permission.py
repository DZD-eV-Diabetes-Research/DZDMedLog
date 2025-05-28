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
    study_data = create_test_study(study_name="TestGetPermissionStudy", with_events=0)

    # First list permissions to get a permission ID
    permissions = req(f"api/study/{study_data.study.id}/permissions", method="get")

    assert permissions["count"] > 0, "No permissions found to test with"
    permission_id = permissions["items"][0]["id"]

    # Get permission details
    permission = req(
        f"api/study/{study_data.study.id}/permissions/{permission_id}", method="get"
    )

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
        exception_dict_identifier="get permission response",
    )


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
