"""Regression tests for externally visible URL generation behind a TLS proxy.

Issue: with a TLS-terminating reverse proxy in front of the app, the OIDC
`redirect_uri` was built with `http://`, because Starlette derives it from the
request scheme and the proxy talks plain HTTP to the container. The identity
provider then had to whitelist a plaintext callback, and the authorization
code travelled one hop on a cleartext request line.
"""

import os
from urllib.parse import parse_qs, urlparse

import requests
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from medlogserver.api.proxy_headers import ExternalUrlMiddleware
from utils import get_medlogserver_base_url
from statics import OIDC_TEST_PROVIDER_SLUG


# ── Unit tests on the middleware ──────────────────────────────────────────────
# These cover the SERVER_PROTOCOL branch, which cannot be exercised against the
# shared live test server without restarting it with a different environment.

TRAEFIK_HEADERS = {
    "x-forwarded-proto": "https",
    "x-forwarded-host": "gds.medlog.dzd-ev.org",
    "x-forwarded-for": "203.0.113.9",
}


def _probe_client(peer: str, trusted_proxies, forced_scheme):
    async def callback(request):
        return JSONResponse({})

    async def probe(request):
        return JSONResponse(
            {
                "url_for": str(request.url_for("callback")),
                "base_url": str(request.base_url),
                "client": request.client.host,
            }
        )

    app = Starlette(
        routes=[Route("/probe", probe), Route("/cb", callback, name="callback")]
    )
    app.add_middleware(
        ExternalUrlMiddleware,
        trusted_proxies=trusted_proxies,
        forced_scheme=forced_scheme,
    )
    return TestClient(app, base_url="http://testserver", client=(peer, 5000))


def test_server_protocol_https_forces_https_urls():
    """SERVER_PROTOCOL=https is authoritative even with no forwarded headers.

    This is the exact production case: traefik sits at 10.33.0.200 and is not
    in the default trusted-proxy list, so nothing but the config can tell the
    app it is reachable over HTTPS.
    """
    client = _probe_client(
        "10.33.0.200", trusted_proxies=["127.0.0.1", "::1"], forced_scheme="https"
    )
    result = client.get("/probe").json()
    assert result["url_for"].startswith("https://"), result
    assert result["base_url"].startswith("https://"), result


def test_forwarded_proto_from_trusted_proxy_is_honoured():
    client = _probe_client(
        "10.33.0.200", trusted_proxies=["10.33.0.0/24"], forced_scheme="http"
    )
    result = client.get("/probe", headers=TRAEFIK_HEADERS).json()
    assert result["url_for"] == "https://gds.medlog.dzd-ev.org/cb", result
    # X-Forwarded-For: session records must show the real client, not the proxy
    assert result["client"] == "203.0.113.9", result


def test_forwarded_headers_from_untrusted_peer_are_ignored():
    """Anyone can send these headers; only a configured proxy is believed."""
    client = _probe_client(
        "198.51.100.7", trusted_proxies=["10.33.0.0/24"], forced_scheme="http"
    )
    result = client.get("/probe", headers=TRAEFIK_HEADERS).json()
    assert result["url_for"] == "http://testserver/cb", result
    assert result["client"] == "198.51.100.7", result


def test_plain_local_development_is_untouched():
    """Default config on plain http must not be rewritten to https."""
    client = _probe_client(
        "127.0.0.1", trusted_proxies=["127.0.0.1", "::1"], forced_scheme="http"
    )
    result = client.get("/probe").json()
    assert result["url_for"] == "http://testserver/cb", result
    assert result["base_url"] == "http://testserver/", result


def test_trusted_proxy_forwarding_plain_http_stays_http():
    """A proxy that terminates no TLS must not get its requests upgraded."""
    client = _probe_client(
        "10.33.0.200", trusted_proxies=["10.33.0.0/24"], forced_scheme="http"
    )
    result = client.get(
        "/probe", headers={"x-forwarded-proto": "http", "x-forwarded-host": "app.local"}
    ).json()
    assert result["url_for"] == "http://app.local/cb", result


# ── Integration tests against the live test server ────────────────────────────
# The test server listens on loopback, which is in the default
# SERVER_TRUSTED_PROXIES list, so it honours the forwarded headers we send.


def _skip_if_no_oidc():
    if not os.environ.get("OIDC_MOCK_SERVER_URL"):
        print("SKIP: OIDC mock server not running — skipping OIDC redirect_uri tests")
        return True
    return False


def _authorize_url_redirect_uri(headers) -> str:
    response = requests.get(
        f"{get_medlogserver_base_url()}/api/auth/oidc/login/{OIDC_TEST_PROVIDER_SLUG}/session",
        headers=headers,
        allow_redirects=False,
    )
    assert response.status_code in (302, 303, 307), (
        f"Expected a redirect to the OIDC provider, got {response.status_code}: {response.text}"
    )
    authorize_url = response.headers["location"]
    redirect_uri = parse_qs(urlparse(authorize_url).query).get("redirect_uri")
    assert redirect_uri, f"No redirect_uri in authorize URL: {authorize_url}"
    return redirect_uri[0]


def test_oidc_redirect_uri_uses_https_with_forwarded_proto():
    """The reported bug: redirect_uri must not carry http:// behind a TLS proxy."""
    if _skip_if_no_oidc():
        return

    redirect_uri = _authorize_url_redirect_uri(
        {"X-Forwarded-Proto": "https", "X-Forwarded-Host": "gds.medlog.dzd-ev.org"}
    )
    assert redirect_uri.startswith("https://gds.medlog.dzd-ev.org/"), (
        f"redirect_uri must use the external https URL, got: {redirect_uri}"
    )


def test_oidc_redirect_uri_stays_http_without_forwarded_proto():
    """Plain local development over http must keep working unchanged."""
    if _skip_if_no_oidc():
        return

    redirect_uri = _authorize_url_redirect_uri({})
    assert redirect_uri.startswith("http://"), (
        f"Plain http development must not be upgraded, got: {redirect_uri}"
    )


def test_auth_list_endpoints_use_https_with_forwarded_proto():
    """The login endpoints handed to the frontend share the same defect."""
    response = requests.get(
        f"{get_medlogserver_base_url()}/api/auth/list",
        headers={"X-Forwarded-Proto": "https", "X-Forwarded-Host": "gds.medlog.dzd-ev.org"},
    )
    response.raise_for_status()
    schemes = response.json()
    assert schemes, "expected at least one configured auth scheme"
    for scheme in schemes:
        for key in ("login_endpoint", "registration_endpoint"):
            endpoint = scheme.get(key)
            if endpoint:
                assert endpoint.startswith("https://gds.medlog.dzd-ev.org/"), (
                    f"{key} must use the external https URL, got: {endpoint}"
                )
