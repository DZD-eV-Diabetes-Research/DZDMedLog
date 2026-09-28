"""Tests for settings provided as secret files, e.g. Docker secrets (issue #181).

In-process style (like tests_public_url.py): Config objects are built directly, no
live server involved. Each test points MEDLOG_SECRETS_DIR at its own temporary
directory, and removes the environment variables the test conftest sets for the
live suite wherever a secret file must be the only source of a value.
"""

import json

import pytest
from pydantic_settings import SettingsError

from medlogserver.config import Config


def _write_secret(secrets_dir, name: str, value: str):
    # Docker secret files usually end with a newline, which must not end up in the value.
    (secrets_dir / name).write_text(value + "\n", encoding="utf-8")


def _provider(**overrides) -> dict:
    """A minimally valid OIDC provider config, without CLIENT_SECRET unless given."""
    provider = {
        "PROVIDER_DISPLAY_NAME": "TestProvider",
        "CONFIGURATION_ENDPOINT": "https://idp.example.com/.well-known/openid-configuration",
        "CLIENT_ID": "test-client-id",
    }
    provider.update(overrides)
    return provider


@pytest.fixture
def secrets_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("MEDLOG_SECRETS_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def oidc_env(monkeypatch):
    monkeypatch.setenv("AUTH_OIDC_TOKEN_STORAGE_SECRET", "test-storage-secret")

    def set_providers(providers: list):
        monkeypatch.setenv("AUTH_OIDC_PROVIDERS", json.dumps(providers))

    return set_providers


# ── top-level settings ────────────────────────────────────────────────────────


def test_setting_is_read_from_secret_file(secrets_dir, monkeypatch):
    monkeypatch.delenv("ADMIN_USER_PW", raising=False)
    _write_secret(secrets_dir, "ADMIN_USER_PW", "pw-from-file")

    assert Config().ADMIN_USER_PW.get_secret_value() == "pw-from-file"


def test_secret_file_name_is_case_insensitive(secrets_dir, monkeypatch):
    monkeypatch.delenv("ADMIN_USER_PW", raising=False)
    _write_secret(secrets_dir, "admin_user_pw", "pw-from-file")

    assert Config().ADMIN_USER_PW.get_secret_value() == "pw-from-file"


def test_environment_variable_wins_over_secret_file(secrets_dir, monkeypatch):
    monkeypatch.setenv("ADMIN_USER_PW", "pw-from-env")
    _write_secret(secrets_dir, "ADMIN_USER_PW", "pw-from-file")

    assert Config().ADMIN_USER_PW.get_secret_value() == "pw-from-env"


def test_list_setting_is_read_as_json_from_secret_file(secrets_dir, monkeypatch):
    monkeypatch.delenv("AUTH_OIDC_PROVIDERS", raising=False)
    monkeypatch.setenv("AUTH_OIDC_TOKEN_STORAGE_SECRET", "test-storage-secret")
    _write_secret(
        secrets_dir,
        "AUTH_OIDC_PROVIDERS",
        json.dumps([_provider(CLIENT_SECRET="secret-in-json-file")]),
    )

    providers = Config().AUTH_OIDC_PROVIDERS
    assert len(providers) == 1
    assert providers[0].CLIENT_SECRET.get_secret_value() == "secret-in-json-file"


def test_configured_secrets_dir_must_exist(tmp_path, monkeypatch):
    monkeypatch.setenv("MEDLOG_SECRETS_DIR", str(tmp_path / "does-not-exist"))

    with pytest.raises(SettingsError, match="MEDLOG_SECRETS_DIR"):
        Config()


# ── single OIDC provider values ───────────────────────────────────────────────


def test_oidc_client_secret_is_read_from_indexed_secret_file(secrets_dir, oidc_env):
    oidc_env(
        [
            _provider(PROVIDER_DISPLAY_NAME="First"),
            _provider(PROVIDER_DISPLAY_NAME="Second"),
        ]
    )
    _write_secret(secrets_dir, "AUTH_OIDC_PROVIDERS__0__CLIENT_SECRET", "first-secret")
    _write_secret(secrets_dir, "auth_oidc_providers__1__client_secret", "second-secret")

    first, second = Config().AUTH_OIDC_PROVIDERS
    assert first.CLIENT_SECRET.get_secret_value() == "first-secret"
    assert second.CLIENT_SECRET.get_secret_value() == "second-secret"


def test_oidc_value_in_json_wins_over_indexed_secret_file(secrets_dir, oidc_env):
    oidc_env([_provider(CLIENT_SECRET="secret-from-json")])
    _write_secret(secrets_dir, "AUTH_OIDC_PROVIDERS__0__CLIENT_SECRET", "from-file")

    provider = Config().AUTH_OIDC_PROVIDERS[0]
    assert provider.CLIENT_SECRET.get_secret_value() == "secret-from-json"


def test_oidc_client_secret_is_still_required(secrets_dir, oidc_env):
    """A provider without CLIENT_SECRET in JSON or as a file keeps failing validation."""
    oidc_env([_provider()])
    _write_secret(secrets_dir, "AUTH_OIDC_PROVIDERS__1__CLIENT_SECRET", "wrong-index")

    with pytest.raises(ValueError, match="CLIENT_SECRET"):
        Config()
