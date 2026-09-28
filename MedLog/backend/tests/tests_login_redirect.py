"""Where the browser is sent after a successful login.

Issue #339: with the Nuxt dev server on :3000 in front of the backend on :8888,
logging in dropped the user back on :8888, which serves whatever stale static
bundle the backend has on disk. The redirect was a bare path, so the browser
resolved it against the *server's* origin rather than the web client's.

Also covers the open redirect that the old handling allowed: `target_path` was
passed straight to `RedirectResponse` on basic login, and only checked for a
leading "/" on the OIDC callback, which "//evil.com" satisfies.
"""

import requests

from medlogserver.api.routes.routes_auth import (
    client_redirect_url,
    is_safe_target_path,
)
from medlogserver.config import Config
from utils import get_medlogserver_base_url
from statics import ADMIN_USER_NAME, ADMIN_USER_PW

config = Config()

EXTERNAL_TARGETS = [
    "//evil.com",
    "//evil.com/path",
    "/\\evil.com",
    "https://evil.com",
    "http://evil.com",
    "path/without/leading/slash",
]


def test_safe_target_paths_are_accepted():
    for target in ("/", "/studies", "/studies/1?tab=intake"):
        assert is_safe_target_path(target), target


def test_external_target_paths_are_rejected():
    for target in EXTERNAL_TARGETS:
        assert not is_safe_target_path(target), target


def test_client_redirect_url_is_absolute_and_on_the_client():
    """A bare path would resolve against the server, not the web client."""
    url = client_redirect_url("/studies/1")
    assert url == f"{str(config.CLIENT_URL).rstrip('/')}/studies/1"
    assert url.startswith(("http://", "https://")), url


def test_client_redirect_url_falls_back_to_client_root():
    for target in (None, "", *EXTERNAL_TARGETS):
        url = client_redirect_url(target)
        assert url == f"{str(config.CLIENT_URL).rstrip('/')}/", (target, url)


def test_basic_login_redirects_to_the_client_url():
    response = requests.post(
        f"{get_medlogserver_base_url()}/api/auth/basic/login/session",
        json={"username": ADMIN_USER_NAME, "password": ADMIN_USER_PW},
        params={"target_path": "/studies"},
        allow_redirects=False,
    )
    assert response.status_code == 303, response.text
    location = response.headers["location"]
    assert location == f"{str(config.CLIENT_URL).rstrip('/')}/studies", location


def test_basic_login_does_not_redirect_off_site():
    """Regression: `target_path` used to reach RedirectResponse unvalidated."""
    for target in EXTERNAL_TARGETS:
        response = requests.post(
            f"{get_medlogserver_base_url()}/api/auth/basic/login/session",
            json={"username": ADMIN_USER_NAME, "password": ADMIN_USER_PW},
            params={"target_path": target},
            allow_redirects=False,
        )
        assert response.status_code == 303, response.text
        location = response.headers["location"]
        assert "evil.com" not in location, (target, location)
        assert location == f"{str(config.CLIENT_URL).rstrip('/')}/", (target, location)
