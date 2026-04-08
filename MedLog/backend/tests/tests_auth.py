from typing import List, Dict
import json
import uuid
import requests
from _single_test_file_runner import run_all_tests_if_test_file_called

if __name__ == "__main__":
    run_all_tests_if_test_file_called()

from utils import (
    req,
    dict_must_contain,
    authorize_for_session,
)
from statics import (
    ADMIN_USER_EMAIL,
    ADMIN_USER_NAME,
)


def test_session_based_logout():
    """Test user CRUD operations"""
    # Create test user data
    from medlogserver.model.user import UserCreate

    test_user_data = {
        "email": "logout.user@example.com",
        "user_name": "logout_test_user",
        "display_name": "logout test User",
    }
    password = "er789wiguz4wgfh"

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

    # set user password
    from medlogserver.api.routes.routes_user_management import set_user_password

    user_id = new_user["id"]
    user_name = new_user["user_name"]
    user_res = req(
        f"/api/user/{user_id}/password",
        method="put",
        f={"new_password": password, "new_password_repeated": password},
    )

    # login with new user
    new_user_session = authorize_for_session(username=user_name, pw=password)
    # test user can access with session
    for cookie in new_user_session.cookies:
        print(repr(cookie.domain), repr(cookie.path), cookie.name)
    res = req("api/user/me", session=new_user_session)
    dict_must_contain(
        res,
        {
            "email": test_user_data["email"],
            "display_name": test_user_data["display_name"],
        },
        exception_dict_identifier="user/me object",
    )

    from medlogserver.api.routes.routes_auth import logout

    # test logout
    res = req("api/auth/logout", session=new_user_session, expected_http_code=200)
