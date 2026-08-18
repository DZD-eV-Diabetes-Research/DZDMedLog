"""Reconstruct the externally visible URL of a request behind a reverse proxy.

Uvicorn only ever sees the hop between the reverse proxy and the container:
plain HTTP on an internal network. Everything Starlette derives from the
request - `request.url_for()`, `request.base_url`, the `Location` header of a
`RedirectResponse` - therefore comes out as `http://...` even when the
deployment is reachable over HTTPS only.

That hurts most in the OIDC login flow: the `redirect_uri` handed to the
identity provider points at a plaintext URL, so the provider has to whitelist
a callback that should not exist, and the authorization code comes back on a
cleartext request line for one hop before the proxy upgrades it.

Two sources are used to repair the ASGI scope, in increasing order of
authority:

1. `X-Forwarded-Proto` / `X-Forwarded-Host` / `X-Forwarded-For`, but only when
   the immediate peer is listed in `SERVER_TRUSTED_PROXIES`. Any client can
   send these headers, so they are worthless unless we know who sent them.
2. `SERVER_PROTOCOL`, which the operator sets to declare how the app is
   reached from outside. It defaults to `http`, so it only ever upgrades a
   request when someone explicitly configured `https`. Plain local
   development on `http://localhost:<port>` is never touched.
"""

from __future__ import annotations

import ipaddress
from typing import List, Optional, Sequence, Set

from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send

from medlogserver.log import get_logger

log = get_logger()

TRUST_ANY = "*"


class TrustedProxies:
    """Membership test for the immediate peer address of a connection.

    Accepts plain addresses ("10.33.0.200"), CIDR networks ("10.33.0.0/24"),
    and the wildcard "*". Anything that does not parse as an address or
    network (a hostname, or the empty string uvicorn uses for unix sockets)
    is compared literally.
    """

    def __init__(self, trusted: Sequence[str]):
        self.trust_any: bool = False
        self.networks: List = []
        self.literals: Set[str] = set()
        for entry in trusted:
            entry = entry.strip()
            if not entry:
                continue
            if entry == TRUST_ANY:
                self.trust_any = True
                continue
            try:
                self.networks.append(ipaddress.ip_network(entry, strict=False))
            except ValueError:
                self.literals.add(entry)

    def __contains__(self, host: Optional[str]) -> bool:
        if self.trust_any:
            return True
        if not host:
            return False
        if host in self.literals:
            return True
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            return False
        return any(address in network for network in self.networks)


def _first_value(header_value: Optional[str]) -> Optional[str]:
    """Take the leftmost entry of a comma separated forwarded header."""
    if not header_value:
        return None
    return header_value.split(",")[0].strip() or None


def _replace_header(scope: Scope, name: bytes, value: bytes) -> None:
    headers = [(key, val) for key, val in scope["headers"] if key != name]
    headers.append((name, value))
    scope["headers"] = headers


class ExternalUrlMiddleware:
    """Pure ASGI middleware, must be the outermost one in the stack.

    Everything downstream - routing, session handling, and every route that
    builds an absolute URL - reads the scope this middleware has already
    corrected.
    """

    # A scope scheme is http/https for requests and ws/wss for websockets.
    _SECURE_SCHEME = {"http": "https", "https": "https", "ws": "wss", "wss": "wss"}
    _PLAIN_SCHEME = {"http": "http", "https": "http", "ws": "ws", "wss": "ws"}

    def __init__(
        self,
        app: ASGIApp,
        trusted_proxies: Sequence[str],
        forced_scheme: Optional[str] = None,
    ):
        self.app = app
        self.trusted_proxies = TrustedProxies(trusted_proxies)
        # Only an explicit "https" is authoritative. Forcing "http" would
        # downgrade a deployment whose proxy correctly announced https.
        self.forced_scheme = forced_scheme if forced_scheme == "https" else None

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            client = scope.get("client")
            if client and client[0] in self.trusted_proxies:
                self._apply_forwarded_headers(scope)
            if self.forced_scheme == "https":
                scope["scheme"] = self._SECURE_SCHEME.get(scope["scheme"], "https")
        await self.app(scope, receive, send)

    def _apply_forwarded_headers(self, scope: Scope) -> None:
        headers = Headers(scope=scope)

        proto = _first_value(headers.get("x-forwarded-proto"))
        if proto == "https":
            scope["scheme"] = self._SECURE_SCHEME.get(scope["scheme"], "https")
        elif proto == "http":
            scope["scheme"] = self._PLAIN_SCHEME.get(scope["scheme"], "http")

        # Starlette builds absolute URLs from the Host header, so rewriting it
        # is what makes X-Forwarded-Host take effect. Traefik and nginx include
        # a non-default port in this value, so no separate X-Forwarded-Port
        # handling is needed.
        host = _first_value(headers.get("x-forwarded-host"))
        if host:
            _replace_header(scope, b"host", host.encode("latin-1"))

        # The peer address is the proxy's. Session records read
        # `request.client.host`, which would otherwise be the proxy for every
        # single user. The leftmost entry is the original client as described
        # by the traefik and nginx docs; it is client-supplied and used for
        # bookkeeping only, never for an authorization decision.
        forwarded_for = _first_value(headers.get("x-forwarded-for"))
        if forwarded_for:
            port = scope["client"][1] if scope.get("client") else 0
            scope["client"] = (forwarded_for, port)
