"""Tests for the user managed API tokens (issue #198).

A logged-in user creates, lists and revokes API tokens for external scripts under
`/api/user/me/api-token`. The feature is off by default (`API_TOKEN_MANAGEMENT_ENABLED`),
the test server runs with it switched on (see conftest.py).

Rules under test:

- Managed tokens are bound to the user, not to the login they were created with. They
  survive a logout, also for OIDC users whose login expires with the access token.
- The management endpoints refuse API tokens, only a browser session may use them.
- Lifetime: omitted -> config default, capped by the config maximum, no non-expiring
  tokens while a maximum is set.
- Revoked tokens and tokens of deactivated users do not authenticate.
- Tokens of OIDC users pause when the last OIDC login is too old.
- A user may only hold a limited number of unexpired tokens.
- User managers can list and revoke the tokens of any user.
- Logout with a token only deletes it if the secret is right.
- Token secrets are hashed with SHA-256 and never logged. Old PBKDF2 hashes still work and
  are upgraded on use.
- Switching the feature off rejects the managed tokens again (tested in-process at the end,
  the live server can not be reconfigured per test).
"""

import asyncio
import datetime
import uuid

import pytest
import requests
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from utils import (
    req,
    authorize_for_access_token,
    authorize_for_session,
    oidc_login_get_session,
    create_test_user,
    get_medlogserver_base_url,
)
from statics import OIDC_TEST_PROVIDER_SLUG


def _status(
    endpoint: str,
    method: str = "get",
    access_token: str | None = None,
    session: requests.Session | None = None,
    json: dict | None = None,
) -> requests.Response:
    """Raw request that does not fall back to the admin token of the test suite."""
    headers = {}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    if session is not None:
        # like utils.req: the cookie jar does not send cookies for "localhost" on its own
        headers["Cookie"] = "; ".join(
            f"{name}={value}" for name, value in session.cookies.get_dict().items()
        )
    return getattr(requests, method)(
        f"{get_medlogserver_base_url()}/{endpoint.lstrip('/')}",
        headers=headers,
        json=json,
    )


def _create_user_session(user_name: str) -> tuple[requests.Session, str]:
    password = f"{user_name}_pw_198"
    user = create_test_user(
        user_name=user_name, password=password, email=f"{user_name}@test.com"
    )
    return authorize_for_session(username=user_name, pw=password), password


def test_config_endpoint_gives_the_client_what_it_needs():
    res = req("api/config/api-token", suppress_auth=True)
    assert res == {
        "enabled": True,
        "default_expiry_days": 30,
        "max_expiry_days": 365,
        "max_tokens_per_user": 20,
        "oidc_login_max_age_days": 30,
        "name_max_length": 128,
        "requires_session_login": True,
    }


def test_create_list_use_and_revoke_token():
    session, _ = _create_user_session("api_token_user_01")

    created = req(
        "api/user/me/api-token",
        method="post",
        b={"name": "Nightly export"},
        session=session,
    )
    assert created["name"] == "Nightly export"
    assert created["created_via"] == "token_management"
    assert created["expired"] is False
    assert created["last_used_at"] is None
    assert created["token"].startswith(f"{created['token_prefix']}.")
    expires_at = datetime.datetime.fromisoformat(created["expires_at"])
    expected = datetime.datetime.now(tz=datetime.UTC).replace(
        tzinfo=None
    ) + datetime.timedelta(days=30)
    assert abs((expires_at - expected).total_seconds()) < 120

    # the token works for the API
    me = _status("api/user/me", access_token=created["token"])
    assert me.status_code == 200, me.text
    assert me.json()["user_name"] == "api_token_user_01"

    # listed without the secret
    tokens = req("api/user/me/api-token", session=session)
    assert [t["id"] for t in tokens] == [created["id"]]
    assert "token" not in tokens[0]
    assert tokens[0]["name"] == "Nightly export"

    # revoke
    res = _status(f"api/user/me/api-token/{created['id']}", "delete", session=session)
    assert res.status_code == 204, res.text
    assert _status("api/user/me", access_token=created["token"]).status_code == 401
    assert req("api/user/me/api-token", session=session) == []
    # revoking twice is a 404
    res = _status(f"api/user/me/api-token/{created['id']}", "delete", session=session)
    assert res.status_code == 404


def test_list_is_newest_first_and_shows_login_tokens():
    session, password = _create_user_session("api_token_user_02")
    first = req(
        "api/user/me/api-token", "post", b={"name": "first"}, session=session
    )
    second = req(
        "api/user/me/api-token", "post", b={"name": "second"}, session=session
    )
    login_token = authorize_for_access_token("api_token_user_02", password)

    tokens = req("api/user/me/api-token", session=session)
    assert [t["name"] for t in tokens[1:]] == ["second", "first"]
    assert tokens[0]["created_via"] == "login"
    assert tokens[0]["name"] is None
    assert login_token.startswith(f"{tokens[0]['token_prefix']}.")


def test_token_survives_logout_of_the_session_that_created_it():
    session, _ = _create_user_session("api_token_user_03")
    created = req(
        "api/user/me/api-token", "post", b={"name": "survivor"}, session=session
    )
    res = _status("api/auth/logout", "post", session=session)
    assert res.status_code == 200, res.text
    assert _status("api/user/me", session=session).status_code == 401
    assert _status("api/user/me", access_token=created["token"]).status_code == 200


def test_oidc_user_token_survives_logout():
    """Tokens bound to the OIDC login would die with the ~1h access token. Managed ones must not."""
    session = oidc_login_get_session(OIDC_TEST_PROVIDER_SLUG, "oidc-api-token-test-user")
    created = req(
        "api/user/me/api-token", "post", b={"name": "oidc script"}, session=session
    )
    assert created["created_via"] == "token_management"
    res = _status("api/auth/logout", "post", session=session)
    assert res.status_code == 200, res.text
    assert _status("api/user/me", session=session).status_code == 401
    me = _status("api/user/me", access_token=created["token"])
    assert me.status_code == 200, me.text
    assert me.json()["user_name"] == "oidc-api-token-test-user"


def test_api_tokens_can_not_manage_api_tokens():
    session, password = _create_user_session("api_token_user_04")
    created = req(
        "api/user/me/api-token", "post", b={"name": "leaky"}, session=session
    )
    for token in (created["token"], authorize_for_access_token("api_token_user_04", password)):
        assert _status("api/user/me/api-token", access_token=token).status_code == 403
        res = _status(
            "api/user/me/api-token", "post", access_token=token, json={"name": "x"}
        )
        assert res.status_code == 403
        res = _status(
            f"api/user/me/api-token/{created['id']}", "delete", access_token=token
        )
        assert res.status_code == 403
    assert len(req("api/user/me/api-token", session=session)) == 2


def test_management_needs_a_login():
    assert _status("api/user/me/api-token").status_code == 401
    assert _status("api/user/me/api-token", "post", json={"name": "x"}).status_code == 401


def test_can_not_revoke_tokens_of_other_users():
    owner_session, _ = _create_user_session("api_token_user_05")
    other_session, _ = _create_user_session("api_token_user_06")
    created = req(
        "api/user/me/api-token", "post", b={"name": "mine"}, session=owner_session
    )
    res = _status(
        f"api/user/me/api-token/{created['id']}", "delete", session=other_session
    )
    assert res.status_code == 404
    assert _status("api/user/me", access_token=created["token"]).status_code == 200


def test_can_not_revoke_non_token_logins():
    """The id of a password or OIDC login must not be deletable through this endpoint."""
    session, _ = _create_user_session("api_token_user_07")
    from medlogserver.db.user_auth import UserAuthCRUD
    from medlogserver.db._session import get_async_session_context
    from medlogserver.model.user_auth import AllowedAuthSchemeType

    me = req("api/user/me", session=session)

    async def basic_login_id():
        async with get_async_session_context() as db_session:
            crud = UserAuthCRUD(session=db_session)
            auth = await crud.get_basic_auth_source_by_user_id(uuid.UUID(me["id"]))
            assert auth.auth_source_type == AllowedAuthSchemeType.basic
            return auth.id

    login_id = asyncio.run(basic_login_id())
    res = _status(f"api/user/me/api-token/{login_id}", "delete", session=session)
    assert res.status_code == 404
    assert req("api/user/me", session=session)["id"] == me["id"]


@pytest.fixture(scope="module")
def validation_session() -> requests.Session:
    session, _ = _create_user_session("api_token_validation_user")
    return session


@pytest.mark.parametrize(
    "body, expected_code",
    [
        ({"name": "too long", "expires_in_days": 366}, 422),
        ({"name": "never expires", "expires_in_days": None}, 422),
        ({"name": "zero", "expires_in_days": 0}, 422),
        ({"name": ""}, 422),
        ({"name": "x" * 129}, 422),
        ({"expires_in_days": 5}, 422),
        ({"name": "beyond hard limit", "expires_in_days": 3651}, 422),
        ({"name": "max", "expires_in_days": 365}, 201),
        ({"name": "one day", "expires_in_days": 1}, 201),
    ],
)
def test_create_validation(validation_session, body, expected_code):
    res = _status(
        "api/user/me/api-token", "post", session=validation_session, json=body
    )
    assert res.status_code == expected_code, res.text
    if expected_code == 201:
        expires_at = datetime.datetime.fromisoformat(res.json()["expires_at"])
        expected = datetime.datetime.now(tz=datetime.UTC).replace(
            tzinfo=None
        ) + datetime.timedelta(days=body["expires_in_days"])
        assert abs((expires_at - expected).total_seconds()) < 120


def test_token_of_deactivated_user_is_rejected():
    session, _ = _create_user_session("api_token_user_08")
    me = req("api/user/me", session=session)
    created = req(
        "api/user/me/api-token", "post", b={"name": "deactivate me"}, session=session
    )
    req(f"/api/user/{me['id']}", method="patch", b={"deactivated": True})
    try:
        assert _status("api/user/me", access_token=created["token"]).status_code == 401
    finally:
        req(f"/api/user/{me['id']}", method="patch", b={"deactivated": False})
    assert _status("api/user/me", access_token=created["token"]).status_code == 200


def test_wrong_secret_with_valid_prefix_is_rejected():
    session, _ = _create_user_session("api_token_user_09")
    created = req(
        "api/user/me/api-token", "post", b={"name": "guessed"}, session=session
    )
    forged = f"{created['token_prefix']}.{'A' * 54}"
    assert _status("api/user/me", access_token=forged).status_code == 401


def test_last_used_at_is_recorded():
    session, _ = _create_user_session("api_token_user_10")
    created = req(
        "api/user/me/api-token", "post", b={"name": "used"}, session=session
    )
    assert _status("api/user/me", access_token=created["token"]).status_code == 200
    (listed,) = req("api/user/me/api-token", session=session)
    last_used_at = datetime.datetime.fromisoformat(listed["last_used_at"])
    now = datetime.datetime.now(tz=datetime.UTC).replace(tzinfo=None)
    assert abs((now - last_used_at).total_seconds()) < 120


def test_logout_with_a_forged_token_does_not_delete_it():
    """The token prefix is listed in the token management, it is not a secret."""
    session, _ = _create_user_session("api_token_user_11")
    created = req(
        "api/user/me/api-token", "post", b={"name": "victim"}, session=session
    )
    forged = f"{created['token_prefix']}.{'A' * 54}"
    assert _status("api/auth/logout", "post", access_token=forged).status_code == 200
    assert _status("api/user/me", access_token=created["token"]).status_code == 200

    # the owner can still log the token out
    res = _status("api/auth/logout", "post", access_token=created["token"])
    assert res.status_code == 200
    assert _status("api/user/me", access_token=created["token"]).status_code == 401


def test_token_count_is_limited_per_user():
    session, password = _create_user_session("api_token_user_12")
    # tokens from the token login do not count
    authorize_for_access_token("api_token_user_12", password)
    created = [
        req("api/user/me/api-token", "post", b={"name": f"t{i}"}, session=session)
        for i in range(20)
    ]
    res = _status("api/user/me/api-token", "post", session=session, json={"name": "t21"})
    assert res.status_code == 409, res.text

    res = _status(f"api/user/me/api-token/{created[0]['id']}", "delete", session=session)
    assert res.status_code == 204
    res = _status("api/user/me/api-token", "post", session=session, json={"name": "t21"})
    assert res.status_code == 201, res.text


def test_user_manager_can_list_and_revoke_tokens_of_a_user():
    session, _ = _create_user_session("api_token_user_13")
    me = req("api/user/me", session=session)
    created = req(
        "api/user/me/api-token", "post", b={"name": "leaked"}, session=session
    )

    # `req` without session authenticates as the admin of the test suite
    tokens = req(f"api/user/{me['id']}/api-token")
    assert [t["id"] for t in tokens] == [created["id"]]
    assert "token" not in tokens[0]

    # a normal user can not use the endpoints
    other_session, _ = _create_user_session("api_token_user_14")
    assert _status(f"api/user/{me['id']}/api-token", session=other_session).status_code == 403
    res = _status(
        f"api/user/{me['id']}/api-token/{created['id']}", "delete", session=other_session
    )
    assert res.status_code == 403

    assert _status(f"api/user/{uuid.uuid4()}/api-token", access_token=_admin_token()).status_code == 404
    # the token id must belong to the user in the path
    other_me = req("api/user/me", session=other_session)
    res = _status(
        f"api/user/{other_me['id']}/api-token/{created['id']}",
        "delete",
        access_token=_admin_token(),
    )
    assert res.status_code == 404

    res = _status(
        f"api/user/{me['id']}/api-token/{created['id']}",
        "delete",
        access_token=_admin_token(),
    )
    assert res.status_code == 204, res.text
    assert _status("api/user/me", access_token=created["token"]).status_code == 401
    assert req(f"api/user/{me['id']}/api-token") == []


def _admin_token() -> str:
    from utils import get_access_token

    return get_access_token()


def test_oidc_login_records_the_login_time():
    session = oidc_login_get_session(OIDC_TEST_PROVIDER_SLUG, "oidc-api-token-test-user")
    me = req("api/user/me", session=session)
    last_login = datetime.datetime.fromisoformat(me["last_oidc_login_at"])
    now = datetime.datetime.now(tz=datetime.UTC).replace(tzinfo=None)
    assert abs((now - last_login).total_seconds()) < 120


# ── In-process: feature switched off ─────────────────────────────────────────


class _FakeUserAuthCRUD:
    def __init__(self, token):
        self.token = token

    async def get_api_token_by_id(self, token_id, raise_exception_if_none=None):
        return self.token if token_id == self.token.api_token_id else None

    async def get(self, id_, raise_exception_if_none=None):
        return None

    async def list_api_tokens_by_user_id(self, user_id):
        return [self.token]

    async def record_api_token_use(self, user_auth, token):
        pass


def _managed_token():
    from medlogserver.model.user_auth import (
        UserAuth,
        UserAuthCreate,
        AllowedAuthSchemeType,
    )

    create = UserAuthCreate(
        user_id=uuid.uuid4(),
        auth_source_type=AllowedAuthSchemeType.api_token,
        api_token_name="in process",
    )
    create.generate_api_token()
    return UserAuth.from_update_or_create_object(create), create.get_api_token()


def test_switching_the_feature_off_rejects_managed_tokens(monkeypatch):
    from medlogserver.api.auth import security

    user_auth, plain_token = _managed_token()
    crud = _FakeUserAuthCRUD(user_auth)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=plain_token)

    def authenticate():
        return asyncio.run(
            security.get_current_user_auth(
                request=None,
                user_session_crud=None,
                user_auth_crud=crud,
                api_token=credentials,
            )
        )

    monkeypatch.setattr(security.config, "API_TOKEN_MANAGEMENT_ENABLED", True)
    assert authenticate().id == user_auth.id

    monkeypatch.setattr(security.config, "API_TOKEN_MANAGEMENT_ENABLED", False)
    with pytest.raises(HTTPException) as e:
        authenticate()
    assert e.value.status_code == 401


def test_token_whose_source_login_is_gone_is_rejected():
    """Was a 500 (AttributeError on None) before. Must be a plain 401."""
    from medlogserver.api.auth import security

    user_auth, plain_token = _managed_token()
    user_auth.api_token_source_user_auth_id = uuid.uuid4()
    with pytest.raises(HTTPException) as e:
        asyncio.run(
            security.get_current_user_auth(
                request=None,
                user_session_crud=None,
                user_auth_crud=_FakeUserAuthCRUD(user_auth),
                api_token=HTTPAuthorizationCredentials(
                    scheme="Bearer", credentials=plain_token
                ),
            )
        )
    assert e.value.status_code == 401


def test_switched_off_management_endpoints_answer_403(monkeypatch):
    from medlogserver.api.routes import routes_user
    from medlogserver.model.api_only.api_token import ApiTokenCreate

    user_auth, _ = _managed_token()
    crud = _FakeUserAuthCRUD(user_auth)
    user = type("FakeUser", (), {"id": user_auth.user_id})()
    monkeypatch.setattr(routes_user.config, "API_TOKEN_MANAGEMENT_ENABLED", False)

    calls = [
        routes_user.list_my_api_tokens(current_user=user, user_auth_crud=crud),
        routes_user.create_my_api_token(
            token_create=ApiTokenCreate(name="x"),
            current_user=user,
            user_auth_crud=crud,
        ),
        routes_user.revoke_my_api_token(
            api_token_id=user_auth.id, current_user=user, user_auth_crud=crud
        ),
    ]
    for call in calls:
        with pytest.raises(HTTPException) as e:
            asyncio.run(call)
        assert e.value.status_code == 403


# ── Config validation ─────────────────────────────────────────────────────────


def _config(**overrides):
    from medlogserver.config import Config

    overrides.setdefault("AUTH_OIDC_PROVIDERS", [])
    overrides.setdefault("AUTH_OIDC_TOKEN_STORAGE_SECRET", "test-storage-secret")
    return Config(**overrides)


def test_config_defaults_are_off_and_bounded(monkeypatch):
    monkeypatch.delenv("API_TOKEN_MANAGEMENT_ENABLED", raising=False)
    config = _config()
    assert config.API_TOKEN_MANAGEMENT_ENABLED is False
    assert config.API_TOKEN_MANAGEMENT_DEFAULT_EXPIRY_DAYS == 30
    assert config.API_TOKEN_MANAGEMENT_MAX_EXPIRY_DAYS == 365


@pytest.mark.parametrize(
    "default_days, max_days, valid",
    [
        (30, 365, True),
        (365, 365, True),
        (400, 365, False),
        (None, 365, False),
        (30, None, True),
        (None, None, True),
    ],
)
def test_config_default_expiry_must_fit_the_maximum(default_days, max_days, valid):
    kwargs = dict(
        API_TOKEN_MANAGEMENT_DEFAULT_EXPIRY_DAYS=default_days,
        API_TOKEN_MANAGEMENT_MAX_EXPIRY_DAYS=max_days,
    )
    if valid:
        _config(**kwargs)
    else:
        with pytest.raises(ValueError):
            _config(**kwargs)


def test_create_model_caps_the_lifetime():
    """With `API_TOKEN_MANAGEMENT_MAX_EXPIRY_DAYS=None` a huge value was a 500 (timedelta overflow)."""
    from pydantic import ValidationError
    from medlogserver.model.api_only.api_token import ApiTokenCreate

    with pytest.raises(ValidationError):
        ApiTokenCreate(name="x", expires_in_days=10**10)
    with pytest.raises(ValueError):
        _config(API_TOKEN_MANAGEMENT_MAX_EXPIRY_DAYS=3651)


# ── In-process: OIDC login age ────────────────────────────────────────────────


class _FakeUserCRUD:
    def __init__(self, user):
        self.user = user

    async def get(self, user_id, show_deactivated=False, raise_exception_if_none=None):
        return self.user


def _authenticate_user(monkeypatch, last_oidc_login_at, max_age_days=30, token=None):
    from medlogserver.api.auth import security
    from medlogserver.model.user import User

    user_auth, plain_token = token or _managed_token()
    user = User(id=user_auth.user_id, user_name="oidc-age-user", last_oidc_login_at=last_oidc_login_at)
    monkeypatch.setattr(security.config, "API_TOKEN_MANAGEMENT_ENABLED", True)
    monkeypatch.setattr(
        security.config, "API_TOKEN_MANAGEMENT_OIDC_LOGIN_MAX_AGE_DAYS", max_age_days
    )
    return asyncio.run(
        security.get_current_user(
            request=None,
            user_session_crud=None,
            user_auth_crud=_FakeUserAuthCRUD(user_auth),
            user_crud=_FakeUserCRUD(user),
            api_token=HTTPAuthorizationCredentials(scheme="Bearer", credentials=plain_token),
        )
    )


def _days_ago(days):
    return datetime.datetime.now(tz=datetime.UTC).replace(tzinfo=None) - datetime.timedelta(days=days)


def test_managed_token_pauses_when_the_oidc_login_is_too_old(monkeypatch):
    assert _authenticate_user(monkeypatch, _days_ago(29)).user_name == "oidc-age-user"
    with pytest.raises(HTTPException) as e:
        _authenticate_user(monkeypatch, _days_ago(31))
    assert e.value.status_code == 401
    assert "Log in" in e.value.detail


def test_oidc_login_age_does_not_affect_other_users_or_a_disabled_check(monkeypatch):
    # never logged in via OIDC: a local user
    assert _authenticate_user(monkeypatch, None).user_name == "oidc-age-user"
    # check disabled
    assert _authenticate_user(monkeypatch, _days_ago(400), max_age_days=None)


# ── In-process: hashing and logging ──────────────────────────────────────────


class _FakeDbSession:
    def __init__(self):
        self.commits = 0

    def add(self, obj):
        pass

    async def commit(self):
        self.commits += 1


def test_plain_token_is_hidden_in_the_create_object_repr():
    from medlogserver.model.user_auth import UserAuthCreate, AllowedAuthSchemeType

    create = UserAuthCreate(
        user_id=uuid.uuid4(), auth_source_type=AllowedAuthSchemeType.api_token
    )
    create.generate_api_token()
    secret = create.get_api_token().split(".", 1)[1]
    assert secret not in repr(create)
    assert secret not in str(create.model_dump())


def test_new_tokens_are_hashed_with_sha256():
    import hashlib

    user_auth, plain_token = _managed_token()
    secret = plain_token.split(".", 1)[1]
    assert user_auth.api_token_hashed == hashlib.sha256(secret.encode()).hexdigest()
    assert not user_auth.api_token_hash_is_legacy()
    assert user_auth.verify_api_token(plain_token)
    assert not user_auth.verify_api_token(f"{user_auth.api_token_id}.{'A' * 54}")


def test_legacy_pbkdf2_token_still_works_and_gets_rehashed():
    from medlogserver.db.user_auth import UserAuthCRUD
    from medlogserver.model.user_auth import _hash_api_token_legacy_pbkdf2

    user_auth, plain_token = _managed_token()
    secret = plain_token.split(".", 1)[1]
    user_auth.api_token_hashed = _hash_api_token_legacy_pbkdf2(secret, user_auth.salt)
    assert user_auth.api_token_hash_is_legacy()
    assert not user_auth.verify_api_token(f"{user_auth.api_token_id}.{'A' * 54}")
    assert user_auth.verify_api_token(plain_token)

    db_session = _FakeDbSession()
    crud = UserAuthCRUD(session=db_session)
    asyncio.run(crud.record_api_token_use(user_auth, plain_token))
    assert not user_auth.api_token_hash_is_legacy()
    assert user_auth.verify_api_token(plain_token)
    assert user_auth.api_token_last_used_at is not None
    assert db_session.commits == 1

    # within the write interval nothing is written again
    asyncio.run(crud.record_api_token_use(user_auth, plain_token))
    assert db_session.commits == 1


def test_token_secrets_do_not_end_up_in_debug_logs():
    """The beta instance runs with LOG_LEVEL=DEBUG."""
    import logging
    from medlogserver import log as log_module
    from medlogserver.api.auth.utils import (
        validate_api_token,
        get_access_token_expires_at_value_from_token,
    )
    from medlogserver.db.user_auth import UserAuthCRUD

    records = []

    class Collect(logging.Handler):
        def emit(self, record):
            records.append(record.getMessage())

    handler = Collect(level=logging.DEBUG)
    loggers = list(log_module.active_loggers_store.values())
    old_levels = [logger.level for logger in loggers]
    for logger in loggers:
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
    try:
        user_auth, plain_token = _managed_token()
        secret = plain_token.split(".", 1)[1]
        crud = UserAuthCRUD(session=_FakeDbSession())
        crud.get_api_token_by_id = _FakeUserAuthCRUD(user_auth).get_api_token_by_id
        asyncio.run(
            validate_api_token(
                token=plain_token,
                not_authenticated_exception=HTTPException(status_code=401),
                user_auth_crud=crud,
            )
        )
        get_access_token_expires_at_value_from_token(
            {"refresh_token": "refresh-secret-xyz", "expires_at": 1, "userinfo": {"exp": 1}}
        )
        # a failing attempt logs at debug level, proves the capture works
        with pytest.raises(HTTPException):
            asyncio.run(
                validate_api_token(
                    token=f"{user_auth.api_token_id}.{secret[::-1]}",
                    not_authenticated_exception=HTTPException(status_code=401),
                    user_auth_crud=crud,
                )
            )
    finally:
        for logger, level in zip(loggers, old_levels):
            logger.removeHandler(handler)
            logger.setLevel(level)
    assert "Token verification failed" in records, records
    joined = "\n".join(records)
    assert secret not in joined
    assert "refresh-secret-xyz" not in joined
