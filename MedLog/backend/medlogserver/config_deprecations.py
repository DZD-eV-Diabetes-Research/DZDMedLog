"""Backwards compatibility shims for deprecated configuration settings.

Everything in this module exists only to keep pre-`PUBLIC_URL` deployments
working. It is deliberately isolated so that dropping support later is a
mechanical deletion rather than an archaeology exercise.

## Why `PUBLIC_URL` replaced the old settings

The externally visible URL used to be assembled from three settings that each
had a second, unrelated job:

    SERVER_PROTOCOL + SERVER_HOSTNAME + SERVER_LISTENING_PORT

`SERVER_LISTENING_PORT` is the port the process *binds*, but it was also spliced
into the public URL, and only the values 80 and 443 suppressed the `:port`
suffix. A deployment behind a TLS proxy therefore had to set
`SERVER_LISTENING_PORT=443` - not because it wanted to bind 443, but because
that was the only way to stop `https://example.org:8888` from being generated.
The container then served plaintext HTTP on port 443, which made its own
healthcheck read `wget http://localhost:443` and look broken.

`PUBLIC_URL` states the external URL directly, and the listening settings go
back to meaning only "where the socket is".

## Removal checklist

When the deprecated style is declared out of order:

1. Delete this module.
2. In `config.py`, delete the `SERVER_PROTOCOL` and `SERVER_HOSTNAME` fields,
   the `config_deprecations` import, and the deprecation branch of
   `resolve_public_url()` (marked with `# DEPRECATED`), leaving `PUBLIC_URL`
   required.
3. In `app.py`, delete the `log_config_deprecations()` call.
4. Delete `ENV SERVER_HOSTNAME=localhost` from the `Dockerfile`.
5. Drop the deprecation tests in `tests/tests_public_url.py` (they are grouped
   under a single marked section).

Nothing else in the codebase reads the deprecated settings: every consumer goes
through `Config.PUBLIC_URL` or `Config.get_server_url()`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:  # pragma: no cover - import cycle guard, config imports us
    from medlogserver.config import Config


# Deprecated setting -> what replaces it. Used for the startup warning only.
DEPRECATED_SETTINGS = {
    "SERVER_PROTOCOL": "PUBLIC_URL",
    "SERVER_HOSTNAME": "PUBLIC_URL",
}


def public_url_from_deprecated_settings(config: "Config") -> str:
    """Rebuild the pre-`PUBLIC_URL` external URL, bug-for-bug.

    This reproduces the historical `get_server_url()` exactly, including the
    listening port leaking into the public URL, so that upgrading without
    touching the configuration cannot change any generated URL.
    """
    if config.SERVER_PROTOCOL is not None:
        protocol = config.SERVER_PROTOCOL
    elif config.SERVER_LISTENING_PORT == 443:
        protocol = "https"
    else:
        protocol = "http"

    port = ""
    if config.SERVER_LISTENING_PORT not in [80, 443]:
        port = f":{config.SERVER_LISTENING_PORT}"

    return f"{protocol}://{config.SERVER_HOSTNAME}{port}"


def collect_deprecation_warnings(config: "Config", public_url_is_explicit: bool) -> List[str]:
    """Describe any deprecated settings in use, for logging at startup.

    Returns an empty list for a configuration that is already fully migrated,
    which is the signal that this whole module can eventually go away.
    """
    messages: List[str] = []
    settings_in_use = [
        name for name in DEPRECATED_SETTINGS if name in config.model_fields_set
    ]
    if not settings_in_use:
        return messages

    if public_url_is_explicit:
        # Already migrated: the deprecated settings are inert, PUBLIC_URL wins and
        # the effective value is logged at startup either way. Staying quiet here
        # matters because the Docker image itself sets SERVER_HOSTNAME, so warning
        # would nag every migrated container about a value it never chose.
        return messages

    listed = ", ".join(sorted(settings_in_use))
    messages.append(
        f"Deprecated setting(s) {listed} are in use. Replace them with a single "
        f"PUBLIC_URL='{config.PUBLIC_URL}'. Support for the old settings will be "
        f"removed in a future release."
    )
    if config.SERVER_LISTENING_PORT not in (80, 443):
        messages.append(
            f"The listening port {config.SERVER_LISTENING_PORT} is part of the derived "
            f"public URL '{config.PUBLIC_URL}'. If that is not how the app is reached "
            f"from outside, set PUBLIC_URL explicitly - it is independent of the port "
            f"the server binds."
        )
    return messages
