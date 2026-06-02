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
    OIDC_TEST_STUDY_ADMIN_GROUP,
    OIDC_TEST_NONEXISTENT_STUDY_NAME,
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

    # The study must exist before login. AUTO_CREATE_STUDY_FROM_MAPPING means a
    # previous test may have already created it, so use get-or-create.
    study_id = _get_or_create_study(OIDC_TEST_STUDY_NAME)

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


# ---------------------------------------------------------------------------
# Helpers shared by the source-tracking tests below
# ---------------------------------------------------------------------------

def _get_or_create_study(study_name: str) -> str:
    """Return study_id, creating the study if it doesn't exist yet."""
    from medlogserver.model.study import StudyCreateAPI

    resp = req(
        "api/study",
        method="post",
        b=StudyCreateAPI(display_name=study_name).model_dump(exclude_unset=True),
        tolerated_error_codes=[409],
    )
    if "id" in resp:
        return resp["id"]
    studies_page = req("api/study")
    study = next(
        (s for s in studies_page["items"] if s["display_name"] == study_name), None
    )
    assert study is not None, f"Study '{study_name}' not found after 409"
    return study["id"]


def _set_mock_user(mock_url: str, sub: str, groups: list, email_verified: bool = True):
    _requests.put(
        f"{mock_url}/users/{sub}",
        json={
            "sub": sub,
            "userinfo": {
                "name": sub,
                "email": f"{sub}@test.com",
                "email_verified": email_verified,
                "given_name": sub,
                "groups": groups,
            },
        },
    ).raise_for_status()


def test_oidc_manual_flag_outside_oidc_scope_survives_revocation():
    """A permission flag set manually by a user manager is never touched by OIDC.

    OIDC only owns flags it is configured to manage (from STUDY_PERMISSION_MAPPING).
    Flags outside that scope — even on the same permission record — must survive when
    OIDC revokes its own grants.

    Scenario:
      - OIDC manages is_study_interviewer via group membership.
      - A user manager also grants is_study_admin manually.
      - User leaves the OIDC group.
      - Re-login: is_study_interviewer is revoked; is_study_admin is preserved.
    """
    if _skip_if_no_oidc():
        return

    mock_url = os.environ["OIDC_MOCK_SERVER_URL"]
    sub = "oidc-perm-source-test-user-a"
    study_id = _get_or_create_study(OIDC_TEST_STUDY_NAME)

    # First login — user in interviewer group → gets is_study_interviewer via OIDC
    _set_mock_user(mock_url, sub, groups=[OIDC_TEST_INTERVIEWER_GROUP])
    token = oidc_login_get_token(OIDC_TEST_PROVIDER_SLUG, sub)
    me = req("api/user/me", access_token=token)
    user_id = me["id"]

    perm = req(f"api/study/{study_id}/permissions/{user_id}")
    assert perm["is_study_interviewer"] is True
    assert "is_study_interviewer" in perm["oidc_managed_permissions"]
    print(f"  ✓ First login: is_study_interviewer=True (OIDC), oidc_managed={perm['oidc_managed_permissions']}")

    # User manager grants is_study_admin manually (not an OIDC-managed flag)
    req(
        f"api/study/{study_id}/permissions/{user_id}",
        method="put",
        b={"is_study_admin": True},
    )
    perm_after_manual = req(f"api/study/{study_id}/permissions/{user_id}")
    assert perm_after_manual["is_study_admin"] is True
    # is_study_admin is outside OIDC scope — must NOT appear in oidc_managed_permissions
    assert "is_study_admin" not in perm_after_manual["oidc_managed_permissions"]
    print(f"  ✓ Manual grant: is_study_admin=True, oidc_managed still={perm_after_manual['oidc_managed_permissions']}")

    # User leaves the OIDC interviewer group
    _set_mock_user(mock_url, sub, groups=[])
    oidc_login_get_token(OIDC_TEST_PROVIDER_SLUG, sub)

    perm2 = req(f"api/study/{study_id}/permissions/{user_id}")
    assert perm2["is_study_interviewer"] is False, (
        f"Expected is_study_interviewer to be revoked by OIDC, got: {perm2}"
    )
    assert perm2["is_study_admin"] is True, (
        f"Expected is_study_admin to be preserved (manually set), got: {perm2}"
    )
    print("  ✓ Re-login: is_study_interviewer revoked, is_study_admin preserved")


def test_oidc_manual_override_of_oidc_flag_prevents_revocation():
    """When a user manager explicitly grants a flag that OIDC also manages, OIDC must
    not revoke it on a future login — the user manager's intent takes precedence.

    This validates the Option-A source-tracking mechanism:
    oidc_managed_permissions is cleared for any flag a user manager explicitly sets,
    so OIDC's revocation path skips it.

    Scenario:
      - OIDC grants is_study_interviewer via group membership.
      - User manager explicitly grants is_study_interviewer=True (takes ownership).
      - User leaves the OIDC group.
      - Re-login: is_study_interviewer must remain True (not revoked).
    """
    if _skip_if_no_oidc():
        return

    mock_url = os.environ["OIDC_MOCK_SERVER_URL"]
    sub = "oidc-perm-source-test-user-b"
    study_id = _get_or_create_study(OIDC_TEST_STUDY_NAME)

    # First login — OIDC grants is_study_interviewer
    _set_mock_user(mock_url, sub, groups=[OIDC_TEST_INTERVIEWER_GROUP])
    token = oidc_login_get_token(OIDC_TEST_PROVIDER_SLUG, sub)
    me = req("api/user/me", access_token=token)
    user_id = me["id"]

    perm = req(f"api/study/{study_id}/permissions/{user_id}")
    assert perm["is_study_interviewer"] is True
    assert "is_study_interviewer" in perm["oidc_managed_permissions"]
    print(f"  ✓ First login: is_study_interviewer=True (OIDC), oidc_managed={perm['oidc_managed_permissions']}")

    # User manager explicitly grants is_study_interviewer — takes ownership from OIDC
    req(
        f"api/study/{study_id}/permissions/{user_id}",
        method="put",
        b={"is_study_interviewer": True},
    )
    perm_after_override = req(f"api/study/{study_id}/permissions/{user_id}")
    assert perm_after_override["is_study_interviewer"] is True
    # OIDC ownership must have been stripped by the user-manager update
    assert "is_study_interviewer" not in perm_after_override["oidc_managed_permissions"], (
        f"Expected 'is_study_interviewer' to be removed from oidc_managed_permissions "
        f"after user-manager override, got: {perm_after_override['oidc_managed_permissions']}"
    )
    print(f"  ✓ Manual override: is_study_interviewer=True (user-manager owned), oidc_managed={perm_after_override['oidc_managed_permissions']}")

    # User leaves the OIDC interviewer group
    _set_mock_user(mock_url, sub, groups=[])
    oidc_login_get_token(OIDC_TEST_PROVIDER_SLUG, sub)

    perm2 = req(f"api/study/{study_id}/permissions/{user_id}")
    assert perm2["is_study_interviewer"] is True, (
        f"Expected is_study_interviewer to remain True (user-manager ownership), "
        f"but OIDC revoked it: {perm2}"
    )
    print("  ✓ Re-login after group removal: is_study_interviewer preserved (user-manager owns it)")


def test_oidc_study_permission_partial_downgrade():
    """When a user loses membership in one OIDC group but keeps another, only the
    permissions granted exclusively by the lost group are revoked.

    Scenario:
      - User is in both OIDC_TEST_INTERVIEWER_GROUP and OIDC_TEST_STUDY_ADMIN_GROUP.
      - Both flags are granted on first login.
      - User leaves OIDC_TEST_STUDY_ADMIN_GROUP but stays in OIDC_TEST_INTERVIEWER_GROUP.
      - Re-login: is_study_admin is revoked, is_study_interviewer remains.
    """
    if _skip_if_no_oidc():
        return

    mock_url = os.environ["OIDC_MOCK_SERVER_URL"]
    sub = "oidc-partial-downgrade-test-user"
    study_id = _get_or_create_study(OIDC_TEST_STUDY_NAME)

    # First login — user in both groups
    _set_mock_user(mock_url, sub, groups=[OIDC_TEST_INTERVIEWER_GROUP, OIDC_TEST_STUDY_ADMIN_GROUP])
    token = oidc_login_get_token(OIDC_TEST_PROVIDER_SLUG, sub)
    me = req("api/user/me", access_token=token)
    user_id = me["id"]

    perm = req(f"api/study/{study_id}/permissions/{user_id}")
    assert perm["is_study_interviewer"] is True, f"Expected is_study_interviewer=True, got: {perm}"
    assert perm["is_study_admin"] is True, f"Expected is_study_admin=True, got: {perm}"
    assert "is_study_interviewer" in perm["oidc_managed_permissions"]
    assert "is_study_admin" in perm["oidc_managed_permissions"]
    print(f"  ✓ First login: both flags granted — {perm['oidc_managed_permissions']}")

    # User leaves the admin group, stays in interviewer group
    _set_mock_user(mock_url, sub, groups=[OIDC_TEST_INTERVIEWER_GROUP])
    oidc_login_get_token(OIDC_TEST_PROVIDER_SLUG, sub)

    perm2 = req(f"api/study/{study_id}/permissions/{user_id}")
    assert perm2["is_study_interviewer"] is True, (
        f"Expected is_study_interviewer to remain after partial group removal, got: {perm2}"
    )
    assert perm2["is_study_admin"] is False, (
        f"Expected is_study_admin to be revoked after leaving admin group, got: {perm2}"
    )
    print("  ✓ Partial downgrade: is_study_admin revoked, is_study_interviewer preserved")


def test_oidc_study_permission_multiple_groups_same_study():
    """Multiple OIDC groups can each contribute permissions to the same study.
    The resulting permission is the union of all matched groups.
    """
    if _skip_if_no_oidc():
        return

    mock_url = os.environ["OIDC_MOCK_SERVER_URL"]
    sub = "oidc-multigroup-test-user"
    study_id = _get_or_create_study(OIDC_TEST_STUDY_NAME)

    # Login with both groups simultaneously
    _set_mock_user(mock_url, sub, groups=[OIDC_TEST_INTERVIEWER_GROUP, OIDC_TEST_STUDY_ADMIN_GROUP])
    token = oidc_login_get_token(OIDC_TEST_PROVIDER_SLUG, sub)
    me = req("api/user/me", access_token=token)
    user_id = me["id"]

    perm = req(f"api/study/{study_id}/permissions/{user_id}")
    assert perm["is_study_interviewer"] is True, (
        f"Expected is_study_interviewer=True from {OIDC_TEST_INTERVIEWER_GROUP}, got: {perm}"
    )
    assert perm["is_study_admin"] is True, (
        f"Expected is_study_admin=True from {OIDC_TEST_STUDY_ADMIN_GROUP}, got: {perm}"
    )
    assert set(perm["oidc_managed_permissions"]) == {"is_study_interviewer", "is_study_admin"}, (
        f"Expected both flags in oidc_managed_permissions, got: {perm['oidc_managed_permissions']}"
    )
    print("  ✓ Both groups contributed their permissions to the same study record")


def test_oidc_email_verified_false_is_respected():
    """When the OIDC provider sends email_verified=false the flag must stay False,
    and it must be updated to True if the provider later sends email_verified=true.
    """
    if _skip_if_no_oidc():
        return

    mock_url = os.environ["OIDC_MOCK_SERVER_URL"]
    sub = "oidc-email-unverified-test-user"

    # First login — provider says email is NOT verified
    _set_mock_user(mock_url, sub, groups=[], email_verified=False)
    token = oidc_login_get_token(OIDC_TEST_PROVIDER_SLUG, sub)
    me = req("api/user/me", access_token=token)

    assert me["is_email_verified"] is False, (
        f"Expected is_email_verified=False when provider sends email_verified=false, "
        f"got: {me['is_email_verified']}"
    )
    print("  ✓ First login: is_email_verified=False (provider claim respected)")

    # Provider now marks the email as verified
    _set_mock_user(mock_url, sub, groups=[], email_verified=True)
    token2 = oidc_login_get_token(OIDC_TEST_PROVIDER_SLUG, sub)
    me2 = req("api/user/me", access_token=token2)

    assert me2["is_email_verified"] is True, (
        f"Expected is_email_verified to update to True after provider changed claim, "
        f"got: {me2['is_email_verified']}"
    )
    print("  ✓ Re-login: is_email_verified updated to True")


def test_oidc_auto_creates_study_from_mapping():
    """When AUTO_CREATE_STUDY_FROM_MAPPING is enabled, a study referenced in
    STUDY_PERMISSION_MAPPING that does not yet exist in the DB is created
    automatically on the first login that triggers the mapping.

    The test conftest enables this flag and registers OIDC_TEST_NONEXISTENT_STUDY_NAME
    in the mapping without pre-creating the study. After login the study must exist
    and the user must hold the correct permission.
    """
    if _skip_if_no_oidc():
        return

    mock_url = os.environ["OIDC_MOCK_SERVER_URL"]
    sub = "oidc-auto-create-study-test-user"

    _set_mock_user(mock_url, sub, groups=[OIDC_TEST_INTERVIEWER_GROUP])

    token = oidc_login_get_token(OIDC_TEST_PROVIDER_SLUG, sub)
    me = req("api/user/me", access_token=token)
    assert me["user_name"] == sub

    # The study must now exist (auto-created by oidc_mappings)
    studies_page = req("api/study")
    created_study = next(
        (s for s in studies_page["items"] if s["display_name"] == OIDC_TEST_NONEXISTENT_STUDY_NAME),
        None,
    )
    assert created_study is not None, (
        f"Expected study '{OIDC_TEST_NONEXISTENT_STUDY_NAME}' to be auto-created on OIDC login, "
        f"but it was not found in the study list"
    )
    print(f"  ✓ Study '{OIDC_TEST_NONEXISTENT_STUDY_NAME}' was auto-created on first OIDC login")

    # And the user must have the mapped permission on it
    perm = req(f"api/study/{created_study['id']}/permissions/{me['id']}")
    assert perm["is_study_interviewer"] is True, (
        f"Expected is_study_interviewer=True on auto-created study, got: {perm}"
    )
    print("  ✓ Permission was applied correctly on the auto-created study")
