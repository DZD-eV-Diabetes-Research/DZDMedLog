"""Tests for PUBLIC_URL, the single source of truth for externally visible URLs.

PUBLIC_URL replaces SERVER_PROTOCOL + SERVER_HOSTNAME + the public-URL role of
SERVER_LISTENING_PORT. The old settings still work; the section at the bottom
of this file covers that and can be deleted with them.
"""

import pytest

from medlogserver.config import Config


def build_config(**overrides):
    """Build a Config with the URL settings under test passed explicitly.

    Constructor arguments outrank every environment source in pydantic-settings,
    and land in `model_fields_set` exactly like a real env var would - which is
    what PUBLIC_URL's "was this configured explicitly?" check reads. Values not
    named here still come from the test environment.

    CLIENT_URL defaults to None so that its derivation from PUBLIC_URL is
    observable; the test conftest sets CLIENT_URL in the environment.
    """
    overrides.setdefault("CLIENT_URL", None)
    return Config(**overrides)


# ── PUBLIC_URL ────────────────────────────────────────────────────────────────


def test_public_url_is_authoritative():
    config = build_config(
        PUBLIC_URL="https://medlog.example.com", SERVER_LISTENING_PORT=8888
    )
    assert config.get_server_url() == "https://medlog.example.com"
    assert config.get_public_scheme() == "https"
    assert config.get_public_hostname() == "medlog.example.com"


def test_public_url_is_independent_of_the_listening_port():
    """The old settings spliced the bind port into the public URL; PUBLIC_URL does not.

    This is what lets a container bind 8888 while being served on 443, instead of
    having to bind 443 just to suppress a ':8888' suffix.
    """
    config = build_config(
        PUBLIC_URL="https://medlog.example.com", SERVER_LISTENING_PORT=8888
    )
    assert config.get_server_url() == "https://medlog.example.com"
    assert config.SERVER_LISTENING_PORT == 8888


def test_public_url_keeps_a_non_default_port():
    config = build_config(PUBLIC_URL="https://medlog.example.com:8443")
    assert config.get_server_url() == "https://medlog.example.com:8443"
    assert config.get_public_hostname() == "medlog.example.com:8443"


def test_public_url_trailing_slash_is_normalised():
    config = build_config(PUBLIC_URL="https://medlog.example.com/")
    assert config.get_server_url() == "https://medlog.example.com"


def test_public_url_seeds_client_url():
    config = build_config(PUBLIC_URL="https://medlog.example.com")
    assert config.CLIENT_URL == "https://medlog.example.com"


def test_explicit_client_url_still_wins():
    """Split deployments (Nuxt dev server) keep their separate client URL."""
    config = build_config(
        PUBLIC_URL="https://medlog.example.com", CLIENT_URL="http://localhost:3000"
    )
    assert config.CLIENT_URL == "http://localhost:3000"
    assert config.get_server_url() == "https://medlog.example.com"


@pytest.mark.parametrize(
    "bad_value",
    [
        "medlog.example.com",  # no scheme
        "ftp://medlog.example.com",  # wrong scheme
        "https://",  # no host
        "https://medlog.example.com/medlog",  # sub-path is not supported
    ],
)
def test_invalid_public_url_is_rejected(bad_value):
    with pytest.raises(Exception) as excinfo:
        build_config(PUBLIC_URL=bad_value)
    assert "PUBLIC_URL" in str(excinfo.value)


def test_migrated_config_emits_no_deprecation_warning():
    config = build_config(PUBLIC_URL="https://medlog.example.com")
    assert config.get_config_deprecation_warnings() == []


# ── DEPRECATED settings ───────────────────────────────────────────────────────
# Everything below covers the backwards compatibility shim and is deleted
# together with medlogserver/config_deprecations.py.


def test_deprecated_settings_still_build_the_public_url():
    """The exact shape of the current production deployment must not change."""
    config = build_config(
        SERVER_PROTOCOL="https",
        SERVER_HOSTNAME="gds.medlog.dzd-ev.org",
        SERVER_LISTENING_PORT=443,
    )
    assert config.get_server_url() == "https://gds.medlog.dzd-ev.org"
    assert config.get_public_scheme() == "https"


def test_deprecated_settings_keep_splicing_the_listening_port():
    """Bug-for-bug compatibility: upgrading must not change any generated URL."""
    config = build_config(
        SERVER_PROTOCOL="http",
        SERVER_HOSTNAME="medlog.example.com",
        SERVER_LISTENING_PORT=8888,
    )
    assert config.get_server_url() == "http://medlog.example.com:8888"


def test_deprecated_settings_do_not_force_the_hostname():
    """SERVER_HOSTNAME defaults to the machine name, so it is never forced."""
    config = build_config(
        SERVER_PROTOCOL="https", SERVER_HOSTNAME="gds.medlog.dzd-ev.org"
    )
    assert config.get_public_hostname() is None


def test_deprecated_settings_warn():
    config = build_config(
        SERVER_PROTOCOL="https",
        SERVER_HOSTNAME="gds.medlog.dzd-ev.org",
        SERVER_LISTENING_PORT=443,
    )
    warnings = config.get_config_deprecation_warnings()
    assert len(warnings) == 1
    assert "SERVER_PROTOCOL" in warnings[0] and "SERVER_HOSTNAME" in warnings[0]
    # The warning names the exact replacement value, so migrating is copy-paste.
    assert "PUBLIC_URL='https://gds.medlog.dzd-ev.org'" in warnings[0]


def test_deprecated_settings_warn_about_the_spliced_port():
    config = build_config(
        SERVER_PROTOCOL="https",
        SERVER_HOSTNAME="medlog.example.com",
        SERVER_LISTENING_PORT=8888,
    )
    warnings = config.get_config_deprecation_warnings()
    assert any("8888" in warning for warning in warnings), warnings


def test_public_url_takes_precedence_over_deprecated_settings():
    config = build_config(
        PUBLIC_URL="https://new.example.com",
        SERVER_PROTOCOL="http",
        SERVER_HOSTNAME="old.example.com",
    )
    assert config.get_server_url() == "https://new.example.com"
