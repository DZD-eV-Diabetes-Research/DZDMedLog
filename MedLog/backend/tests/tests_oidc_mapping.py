import os
import requests as _requests
from _single_test_file_runner import run_all_tests_if_test_file_called

if __name__ == "__main__":
    run_all_tests_if_test_file_called()

from utils import (
    req,
    dict_must_contain,
    oidc_login_get_token,
    create_test_study,
)
from statics import (
    OIDC_TEST_PROVIDER_SLUG,
    OIDC_TEST_STUDY_NAME,
    OIDC_TEST_ROLE_GROUP,
)


def _skip_if_no_oidc():
    if not os.environ.get("OIDC_MOCK_SERVER_URL"):
        print("SKIP: OIDC mock server not running — skipping OIDC mapping tests")
        return True
    return False


def test_oidc_role_mapping():
    """ROLE_MAPPING is applied on first login and re-applied (updated) on re-login.

    Covers issue #273: roles must be reapplied on every login, not only on user creation.
    """
    if _skip_if_no_oidc():
        return

    mock_url = os.environ["OIDC_MOCK_SERVER_URL"]
    sub = "oidc-relogin-test-user"

    # First login — user is in OIDC_TEST_ROLE_GROUP → should get medlog-admin role
    token = oidc_login_get_token(OIDC_TEST_PROVIDER_SLUG, sub)
    me = req("api/user/me", access_token=token)
    assert "medlog-admin" in me["roles"], (
        f"Expected 'medlog-admin' in roles after first OIDC login, got: {me['roles']}"
    )
    print(f"  ✓ First login: roles={me['roles']}")

    # Remove the user from the admin group via the mock server
    _requests.put(
        f"{mock_url}/users/{sub}",
        json={
            "sub": sub,
            "userinfo": {
                "name": sub,
                "email": "oidc-relogin-test@test.com",
                "given_name": "OIDC Relogin Test",
                "groups": [],
            },
        },
    ).raise_for_status()

    # Re-login — roles must be updated, not kept from the creation snapshot
    token2 = oidc_login_get_token(OIDC_TEST_PROVIDER_SLUG, sub)
    me2 = req("api/user/me", access_token=token2)
    assert "medlog-admin" not in me2["roles"], (
        f"Expected 'medlog-admin' to be removed after group change, got: {me2['roles']}"
    )
    print(f"  ✓ Re-login after group removal: roles={me2['roles']}")


def test_oidc_study_permission_mapping():
    """STUDY_PERMISSION_MAPPING grants study permissions on login and reapplies them.

    Covers issue #46: permissions derived from OIDC group membership must be
    applied and kept up-to-date on every login.
    """
    if _skip_if_no_oidc():
        return

    sub = "oidc-study-perm-test-user"

    # The study referenced in STUDY_PERMISSION_MAPPING must exist before login
    study_data = create_test_study(study_name=OIDC_TEST_STUDY_NAME, with_events=0)
    study_id = study_data.study.id

    # First login — user is in OIDC_TEST_INTERVIEWER_GROUP → should get is_study_interviewer
    token = oidc_login_get_token(OIDC_TEST_PROVIDER_SLUG, sub)
    # Use the OIDC token only to resolve the user's ID; permission lookup requires admin
    me = req("api/user/me", access_token=token)
    user_id = me["id"]

    # Permission GET requires study-admin or user-manager — use the global admin token
    perm = req(f"api/study/{study_id}/permissions/{user_id}")
    dict_must_contain(
        perm,
        required_keys_and_val={"is_study_interviewer": True},
        exception_dict_identifier="study permission after first OIDC login",
    )
    print(f"  ✓ First login: study permission applied — is_study_interviewer=True")

    # Re-login — permission must still be there (idempotent reapplication)
    oidc_login_get_token(OIDC_TEST_PROVIDER_SLUG, sub)
    perm2 = req(f"api/study/{study_id}/permissions/{user_id}")
    dict_must_contain(
        perm2,
        required_keys_and_val={"is_study_interviewer": True},
        exception_dict_identifier="study permission after re-login",
    )
    print(f"  ✓ Re-login: study permission still applied — is_study_interviewer=True")
