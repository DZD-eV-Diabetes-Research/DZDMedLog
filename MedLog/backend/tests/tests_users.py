from typing import List, Dict
import json

from _single_test_file_runner import run_all_tests_if_test_file_called

if __name__ == "__main__":
    run_all_tests_if_test_file_called()
import requests
from utils import (
    req,
    dict_must_contain,
    list_contains_dict_that_must_contain,
    find_first_dict_in_list,
    create_test_user,
    dictyfy,
    authorize,
)
from statics import ADMIN_USER_EMAIL, ADMIN_USER_NAME, TEST_USER_NAME, TEST_USER_PW


class Helper:
    @classmethod
    def get_user_id_by_username(cls, name: str):
        all_users = req("api/user", q={"incl_deactivated": True})["items"]
        return find_first_dict_in_list(
            all_users,
            required_keys_and_val={"user_name": name},
            raise_if_not_found=False,
        )


def test_user_me():
    res = req("api/user/me")
    dict_must_contain(
        res,
        {"email": ADMIN_USER_EMAIL, "user_name": ADMIN_USER_NAME},
        exception_dict_identifier="user/me object",
    )


def test_user_create_with_no_password(tolerate_existing: bool = True):
    # we need to tolerate existing users, because we do not delete users for now.
    # to be able to rerun tests without reseting the db we just tolerate existing users
    tolerated_error = {"detail": "User allready exists"} if tolerate_existing else None
    from medlogserver.api.routes.routes_user import create_user

    user_init_data = {
        "email": "test_user_wo_pw@test.com",
        "display_name": "aintgot nopw",
        "user_name": TEST_USER_NAME,
    }
    res = req(
        "api/user", "post", b=user_init_data, tolerated_error_body=[tolerated_error]
    )
    if res != tolerated_error:
        dict_must_contain(
            res, user_init_data, required_keys=["created_at", "roles", "id"]
        )
    if res == tolerated_error:
        print("TEST FAILED BUT WITH TOLERATED ERROR: ", res)


def test_duplicate_username_catch():
    # must be run after test_user_create_with_no_password
    try:
        test_user_create_with_no_password(tolerate_existing=False)
    except requests.HTTPError as err:
        if json.loads(err.response.content) != {"detail": "User allready exists"}:
            raise err


def test_user_list_with_deactivted():
    res = req("api/user", q={"incl_deactivated": True})
    list_contains_dict_that_must_contain(
        res["items"],
        {"email": ADMIN_USER_EMAIL, "user_name": ADMIN_USER_NAME},
        exception_dict_identifier="test_user_list admin",
    )
    list_contains_dict_that_must_contain(
        res["items"],
        {"email": "test_user_wo_pw@test.com", "user_name": TEST_USER_NAME},
        exception_dict_identifier="test_user_list ",
    )


def test_user_list_with_active_only():
    res = req("api/user")
    list_contains_dict_that_must_contain(
        res["items"],
        {"email": ADMIN_USER_EMAIL, "user_name": ADMIN_USER_NAME},
        exception_dict_identifier="test_user_list admin",
    )


def test_set_other_user_password_as_admin():
    from medlogserver.model.user import UserCreate, User
    from medlogserver.api.routes.routes_user import create_user

    user_name = "test_set_other_user_password_as_admin"
    password = "rwes79i3qwehkfbdsjh"
    user_create = UserCreate(
        user_name=user_name, email="test_set_other_user_password_as_admin@t.com"
    )
    user_raw = req(
        "api/user",
        method="post",
        b=dictyfy(user_create),
    )

    user = User.model_validate(user_raw)
    # set user password
    req(
        f"/api/user/{user.id}/password",
        method="put",
        b={"new_password": password, "new_password_repeated": password},
    )
    access_token = authorize(user_name, pw=password, set_as_global_default_login=False)
    print("access_token", access_token)
    assert access_token != ""
    assert access_token is not None
    assert " " not in access_token


# def run_all_tests_users():
#    test_user_create_with_no_password()
