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
from statics import (
    ADMIN_USER_EMAIL,
    ADMIN_USER_NAME,
)


def test_endpoint_role_list():
    """Test GET /api/role endpoint"""
    # List available roles
    response = req("api/role", method="get")

    # Should be a list of roles
    assert isinstance(response, list)

    # Each role should have required fields
    for role in response:
        dict_must_contain(
            role,
            required_keys=["role_name", "description"],
            exception_dict_identifier="role item",
        )

    # Should contain at least admin and user manager roles
    role_names = [role["role_name"] for role in response]
    assert "admin" in role_names
    assert "usermanager" in role_names


def test_endpoint_user_crud():
    """Test user CRUD operations"""
    # Create test user data
    test_user_data = {
        "email": "test.user@example.com",
        "display_name": "Test User",
        "password": "securepassword123",
    }

    # Create new user
    new_user = req("api/user", method="post", b=test_user_data)

    dict_must_contain(
        new_user,
        required_keys=["id", "email", "display_name", "created_at"],
        required_keys_and_val={
            "email": test_user_data["email"],
            "display_name": test_user_data["display_name"],
        },
        exception_dict_identifier="create user response",
    )

    user_id = new_user["id"]

    # Update user
    update_data = {
        "display_name": "Updated Test User",
    }

    updated_user = req(f"api/user/{user_id}", method="patch", b=update_data)

    dict_must_contain(
        updated_user,
        required_keys=["id", "email", "display_name", "created_at"],
        required_keys_and_val={
            "display_name": update_data["display_name"],
            "email": test_user_data["email"],
        },
        exception_dict_identifier="update user response",
    )

    # Get user
    user = req(f"api/user/{user_id}", method="get")

    dict_must_contain(
        user,
        required_keys=["id", "email", "display_name", "created_at"],
        required_keys_and_val={
            "id": user_id,
            "email": test_user_data["email"],
            "display_name": update_data["display_name"],
        },
        exception_dict_identifier="get user response",
    )

    # List users
    users = req("api/user", method="get")

    dict_must_contain(
        users,
        required_keys=["total_count", "offset", "count", "items"],
        exception_dict_identifier="list users response",
    )

    # Should contain at least our test user
    assert any(u["id"] == user_id for u in users["items"])

    # Test user role assignment
    role_data = {
        "role": "usermanager",
    }

    role_response = req(f"api/user/{user_id}/role", method="put", b=role_data)

    dict_must_contain(
        role_response,
        required_keys=["id", "email", "display_name", "roles"],
        required_keys_and_val={
            "id": user_id,
            "roles": ["usermanager"],
        },
        exception_dict_identifier="assign role response",
    )

    # Delete user role
    role_delete_response = req(
        f"api/user/{user_id}/role/{role_data['role']}", method="delete"
    )

    dict_must_contain(
        role_delete_response,
        required_keys=["id", "email", "display_name", "roles"],
        required_keys_and_val={
            "id": user_id,
            "roles": [],
        },
        exception_dict_identifier="delete role response",
    )
