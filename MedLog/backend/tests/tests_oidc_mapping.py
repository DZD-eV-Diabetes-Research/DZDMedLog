import os
import requests as _requests

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
    OIDC_TEST_INTERVIEWER_GROUP,
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


def test_oidc_study_permission_revocation_on_group_removal_issue_305():
    """Study permissions derived from OIDC group membership must be revoked when
    the user is removed from the mapped group.

    Confirms the bug: OIDC login only grants study roles but never removes them,
    so revoking group membership does not revoke study access.
    Global roles are replaced correctly; study permissions are not.
    """
    if _skip_if_no_oidc():
        return

    mock_url = os.environ["OIDC_MOCK_SERVER_URL"]
    sub = "oidc-study-perm-revoke-test-user"

    # Resolve the test study — create it if it doesn't exist yet, otherwise find it.
    from medlogserver.model.study import StudyCreateAPI

    study_create_resp = req(
        "api/study",
        method="post",
        b=StudyCreateAPI(display_name=OIDC_TEST_STUDY_NAME).model_dump(exclude_unset=True),
        tolerated_error_codes=[409],
    )
    if "id" in study_create_resp:
        study_id = study_create_resp["id"]
    else:
        # 409 — study already exists; find it in the listing
        studies_page = req("api/study")
        study = next(
            (s for s in studies_page["items"] if s["display_name"] == OIDC_TEST_STUDY_NAME),
            None,
        )
        assert study is not None, (
            f"Study '{OIDC_TEST_STUDY_NAME}' not found after 409 on creation"
        )
        study_id = study["id"]

    # Put the user into the interviewer group on the mock server
    _requests.put(
        f"{mock_url}/users/{sub}",
        json={
            "sub": sub,
            "userinfo": {
                "name": sub,
                "email": "oidc-study-perm-revoke-test@test.com",
                "given_name": "OIDC Study Revoke Test",
                "groups": [OIDC_TEST_INTERVIEWER_GROUP],
            },
        },
    ).raise_for_status()

    # First login — user is in OIDC_TEST_INTERVIEWER_GROUP → must gain is_study_interviewer
    token = oidc_login_get_token(OIDC_TEST_PROVIDER_SLUG, sub)
    me = req("api/user/me", access_token=token)
    user_id = me["id"]

    perm = req(f"api/study/{study_id}/permissions/{user_id}")
    dict_must_contain(
        perm,
        required_keys_and_val={"is_study_interviewer": True},
        exception_dict_identifier="study permission after first OIDC login",
    )
    print(f"  ✓ First login: study permission applied — is_study_interviewer=True")

    # Remove the user from every mapped group on the mock server
    _requests.put(
        f"{mock_url}/users/{sub}",
        json={
            "sub": sub,
            "userinfo": {
                "name": sub,
                "email": "oidc-study-perm-revoke-test@test.com",
                "given_name": "OIDC Study Revoke Test",
                "groups": [],
            },
        },
    ).raise_for_status()

    # Re-login — study permission must be revoked (BUG: currently it is NOT removed)
    oidc_login_get_token(OIDC_TEST_PROVIDER_SLUG, sub)
    perm2 = req(
        f"api/study/{study_id}/permissions/{user_id}",
        tolerated_error_codes=[404],
    )
    # After a correct fix, the permission record is either gone (404 → error body without
    # is_study_interviewer) or updated to False. Either way the flag must not be True.
    assert not perm2.get("is_study_interviewer", False), (
        f"Expected 'is_study_interviewer' to be revoked after the user left "
        f"'{OIDC_TEST_INTERVIEWER_GROUP}', but got: {perm2}"
    )
    print(f"  ✓ Re-login after group removal: is_study_interviewer revoked")


def test_oidc_userinfo_updated_on_relogin_issue_308():
    """User profile fields sourced from OIDC userinfo must be re-applied on every login.

    Confirms issue #308:
    - display_name is taken from the OIDC provider's display-name attribute (given_name in
      test config) only at account creation time and never updated on subsequent logins.
    - is_email_verified is never read from the standard email_verified OIDC claim.
    """
    if _skip_if_no_oidc():
        return

    mock_url = os.environ["OIDC_MOCK_SERVER_URL"]
    sub = "oidc-userinfo-update-test-user"

    # First login — register the user with a known display name and verified email
    _requests.put(
        f"{mock_url}/users/{sub}",
        json={
            "sub": sub,
            "userinfo": {
                "name": sub,
                "email": "oidc-userinfo-update-test@test.com",
                "email_verified": True,
                "given_name": "Original Display Name",
                "groups": [],
            },
        },
    ).raise_for_status()

    token = oidc_login_get_token(OIDC_TEST_PROVIDER_SLUG, sub)
    me = req("api/user/me", access_token=token)

    assert me["display_name"] == "Original Display Name", (
        f"Expected display_name='Original Display Name' after first OIDC login, got: {me['display_name']}"
    )
    print(f"  ✓ First login: display_name='{me['display_name']}'")

    # is_email_verified must reflect the email_verified claim from the OIDC provider
    assert me["is_email_verified"] is True, (
        f"Expected is_email_verified=True because the provider sent email_verified=true, "
        f"got: {me['is_email_verified']}"
    )
    print("  ✓ First login: is_email_verified=True")

    # Change the display name on the mock server (email_verified stays True)
    _requests.put(
        f"{mock_url}/users/{sub}",
        json={
            "sub": sub,
            "userinfo": {
                "name": sub,
                "email": "oidc-userinfo-update-test@test.com",
                "email_verified": True,
                "given_name": "Updated Display Name",
                "groups": [],
            },
        },
    ).raise_for_status()

    # Re-login — display_name must reflect the new value from the OIDC provider (BUG: it does not)
    token2 = oidc_login_get_token(OIDC_TEST_PROVIDER_SLUG, sub)
    me2 = req("api/user/me", access_token=token2)

    assert me2["display_name"] == "Updated Display Name", (
        f"Expected display_name to be updated to 'Updated Display Name' after re-login "
        f"with changed OIDC userinfo, but got: '{me2['display_name']}'"
    )
    print(f"  ✓ Re-login: display_name updated to '{me2['display_name']}'")
