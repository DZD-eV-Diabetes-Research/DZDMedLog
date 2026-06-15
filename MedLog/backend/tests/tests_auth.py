from typing import List, Dict
import json
import uuid
import requests

from utils import (
    req,
    dict_must_contain,
    authorize_for_access_token,
    authorize_for_session,
    oidc_login_get_session,
    create_test_user,
)
from statics import (
    ADMIN_USER_EMAIL,
    ADMIN_USER_NAME,
    OIDC_TEST_PROVIDER_SLUG,
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


def test_oidc_session_logout():
    """OIDC session login sets a cookie; logout invalidates it.

    Verifies that after logout the session cookie is gone and protected
    endpoints reject the session with 401.
    """
    import os

    if not os.environ.get("OIDC_MOCK_SERVER_URL"):
        print("SKIP: OIDC mock server not running — skipping OIDC session logout test")
        return

    sub = "oidc-role-test-user"
    oidc_session = oidc_login_get_session(OIDC_TEST_PROVIDER_SLUG, sub)

    # Session must be valid — user/me returns the OIDC user
    me = req("api/user/me", session=oidc_session)
    assert me["user_name"] == sub, (
        f"Expected user_name='{sub}', got '{me['user_name']}'"
    )

    # Logout — OIDC path returns end_session_url from the mock's end_session endpoint
    logout_res = req(
        "api/auth/logout", method="post", session=oidc_session, expected_http_code=200
    )
    assert logout_res == {"message": "Logged out successfully"}, (
        f"Expected 'end_session_url' in OIDC logout response, got: {logout_res}"
    )

    # Cookie must be cleared after logout
    assert not oidc_session.cookies.get_dict(), (
        f"Expected empty cookie jar after logout, got: {oidc_session.cookies.get_dict()}"
    )

    # Protected endpoint must now reject the old session
    req("api/user/me", session=oidc_session, expected_http_code=401)


def test_deactivated_user_cannot_log_in():
    """A deactivated account must be rejected at login. Reactivating it must
    restore the ability to log in.
    """
    password = "deact_test_pw_6641"
    user = create_test_user(
        user_name="deactivation_test_user",
        password=password,
        email="deactivation_test@test.com",
    )

    # Freshly created user can log in
    token = authorize_for_access_token(
        username=user.user_name, pw=password, set_as_global_default_login=False
    )
    assert token, "Expected a token for active user"
    me = req("api/user/me", access_token=token)
    assert me["user_name"] == user.user_name

    # Deactivate the user via admin
    req(f"/api/user/{user.id}", method="patch", b={"deactivated": True})

    # Login must now be rejected
    import requests as _requests
    from utils import get_medlogserver_base_url

    resp = _requests.post(
        f"{get_medlogserver_base_url()}/api/auth/basic/login/token",
        data={"username": user.user_name, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code in (401, 403), (
        f"Expected 401/403 for deactivated user login, got {resp.status_code}: {resp.text}"
    )
    print(f"  ✓ Deactivated user login rejected with {resp.status_code}")

    # Reactivate and verify login works again
    req(f"/api/user/{user.id}", method="patch", b={"deactivated": False})
    token2 = authorize_for_access_token(
        username=user.user_name, pw=password, set_as_global_default_login=False
    )
    assert token2, "Expected a token after reactivation"
    print("  ✓ Reactivated user can log in again")
