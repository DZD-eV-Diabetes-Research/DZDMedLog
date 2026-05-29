import os
import sys
import json
import time
import threading
import subprocess
import logging
from pathlib import Path

import pytest

logger = logging.getLogger("conftest")

# Add backend/ to sys.path so medlogserver is importable during collection
TESTS_DIR = Path(__file__).parent
BACKEND_DIR = TESTS_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

# Resolve git root so server subprocesses run from there — setuptools_scm's
# get_version() uses CWD as root, so it needs to be the repo root to find .git.
def _find_git_root() -> Path:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(BACKEND_DIR),
            stderr=subprocess.DEVNULL,
        )
        return Path(out.decode().strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return BACKEND_DIR

GIT_ROOT = _find_git_root()

from statics import (
    DB_PATH,
    DOT_ENV_FILE_PATH,
    ADMIN_USER_EMAIL,
    ADMIN_USER_PW,
    ADMIN_USER_NAME,
    DRUG_IMPORTER_ALLOW_MANUAL_UPDATE_DRUG_DB,
    SYSTEM_ANNOUNCEMENTS,
    OIDC_TEST_PROVIDER_DISPLAY_NAME,
    OIDC_TEST_PROVIDER_SLUG,
    OIDC_TEST_STUDY_NAME,
    OIDC_TEST_ROLE_GROUP,
    OIDC_TEST_INTERVIEWER_GROUP,
)


def set_config_for_test_env():
    os.environ["MEDLOG_DOT_ENV_FILE"] = DOT_ENV_FILE_PATH
    sql_database_url = os.getenv("SQL_DATABASE_URL")
    os.environ["SQL_DATABASE_URL"] = (
        sql_database_url
        if sql_database_url is not None
        else f"sqlite+aiosqlite:///{DB_PATH}"
    )
    os.environ["ADMIN_USER_NAME"] = ADMIN_USER_NAME
    os.environ["ADMIN_USER_PW"] = ADMIN_USER_PW
    os.environ["ADMIN_USER_EMAIL"] = ADMIN_USER_EMAIL
    os.environ["SERVER_SESSION_SECRET"] = (
        "asdöghjsekrhsergl669823jsakdgl!32kgsadefghs5gakljghlkej5h30985zu0awgh0j34g093a4jgh09ajg09j340tgjhj45po"
    )
    os.environ["CLIENT_URL"] = "https://localhost:8888"
    os.environ["BRANDING_SUPPORT_EMAIL_ADDRESS"] = "mytest@test.de"
    os.environ["DRUG_IMPORTER_ALLOW_MANUAL_UPDATE_DRUG_DB"] = str(
        DRUG_IMPORTER_ALLOW_MANUAL_UPDATE_DRUG_DB
    )
    os.environ["SYSTEM_ANNOUNCEMENTS"] = json.dumps(SYSTEM_ANNOUNCEMENTS)


# Set env vars at module level so they're in place before any test module is
# imported during pytest's collection phase.
set_config_for_test_env()

_OIDC_TEST_USERS = [
    {
        "sub": "oidc-role-test-user",
        "userinfo": {
            "name": "oidc-role-test-user",
            "email": "oidc-role-test@test.com",
            "given_name": "OIDC Role Test",
            "groups": [OIDC_TEST_ROLE_GROUP],
        },
    },
    {
        "sub": "oidc-relogin-test-user",
        "userinfo": {
            "name": "oidc-relogin-test-user",
            "email": "oidc-relogin-test@test.com",
            "given_name": "OIDC Relogin Test",
            "groups": [OIDC_TEST_ROLE_GROUP],
        },
    },
    {
        "sub": "oidc-study-perm-test-user",
        "userinfo": {
            "name": "oidc-study-perm-test-user",
            "email": "oidc-study-perm-test@test.com",
            "given_name": "OIDC Study Perm Test",
            "groups": [OIDC_TEST_INTERVIEWER_GROUP],
        },
    },
]

_oidc_mock_ctx = None


def _start_oidc_mock():
    global _oidc_mock_ctx
    try:
        import oidc_provider_mock
        import requests as _requests
    except ImportError:
        logger.warning("oidc_provider_mock not installed — skipping OIDC test setup")
        return

    ctx = oidc_provider_mock.run_server_in_thread(port=0)
    server = ctx.__enter__()
    _oidc_mock_ctx = ctx

    mock_url = f"http://localhost:{server.server_port}"
    os.environ["OIDC_MOCK_SERVER_URL"] = mock_url
    logger.info("OIDC mock server started at %s", mock_url)

    for user in _OIDC_TEST_USERS:
        res = _requests.put(f"{mock_url}/users/{user['sub']}", json=user)
        res.raise_for_status()

    provider_config = {
        "PROVIDER_DISPLAY_NAME": OIDC_TEST_PROVIDER_DISPLAY_NAME,
        "CONFIGURATION_ENDPOINT": f"{mock_url}/.well-known/openid-configuration",
        "CLIENT_ID": "test-client-id",
        "CLIENT_SECRET": "test-client-secret",
        "USER_NAME_ATTRIBUTE": "name",
        "USER_DISPLAY_NAME_ATTRIBUTE": "given_name",
        "USER_MAIL_ATTRIBUTE": "email",
        "USER_GROUPS_ATTRIBUTE": "groups",
        "ROLE_MAPPING": {OIDC_TEST_ROLE_GROUP: ["medlog-admin"]},
        "STUDY_PERMISSION_MAPPING": {
            OIDC_TEST_STUDY_NAME: {
                OIDC_TEST_INTERVIEWER_GROUP: ["is_study_interviewer"],
            }
        },
    }
    os.environ["AUTH_OIDC_TOKEN_STORAGE_SECRET"] = "oidc-test-storage-secret-42"
    os.environ["AUTH_OIDC_PROVIDERS"] = json.dumps([provider_config])
    logger.info("OIDC provider configured with slug '%s'", OIDC_TEST_PROVIDER_SLUG)


def _stop_oidc_mock():
    global _oidc_mock_ctx
    if _oidc_mock_ctx is not None:
        _oidc_mock_ctx.__exit__(None, None, None)
        _oidc_mock_ctx = None


MEDLOG_MAIN = BACKEND_DIR / "medlogserver" / "main.py"


def _start_subprocess(label: str, cmd: list) -> subprocess.Popen:
    """Start a subprocess and stream its combined stdout+stderr through the logger."""
    proc = subprocess.Popen(
        cmd,
        env=dict(os.environ),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=str(GIT_ROOT),
    )

    def _stream():
        for raw in proc.stdout:
            line = raw.decode(errors="replace").rstrip()
            if line:
                logger.debug("[%s] %s", label, line)

    threading.Thread(target=_stream, daemon=True, name=f"{label}-logger").start()
    return proc


@pytest.fixture(scope="session", autouse=True)
def live_server():
    import requests
    import urllib3
    from utils import (
        get_medlogserver_base_url,
        get_dot_env_file_variable,
        authorize_for_access_token,
        req,
    )

    reset_db = os.getenv(
        "MEDLOG_TESTS_RESET_DB",
        get_dot_env_file_variable(
            DOT_ENV_FILE_PATH, "MEDLOG_TESTS_RESET_DB", default="True"
        ),
    ).lower() in ("true", "1", "t", "y", "yes")

    if reset_db:
        sql_url = os.getenv("SQL_DATABASE_URL", "")
        if sql_url.startswith("sqlite"):
            Path(DB_PATH).unlink(missing_ok=True)
            logger.info("Deleted test DB at %s", DB_PATH)
        else:
            logger.warning(
                "RESET_DB enabled but database is not SQLite — reset must be done externally."
            )

    # Start OIDC mock before server processes so OIDC env vars are in os.environ
    _start_oidc_mock()

    # Run main.py as a real script (not -c) so __main__.__file__ is set correctly.
    # This mirrors exactly how run_dev_backend_server_with_oidc.sh starts the server.
    logger.info("Starting MedLog server subprocess...")
    server_proc = _start_subprocess("server", [sys.executable, str(MEDLOG_MAIN)])
    logger.info("Starting background worker subprocess...")
    worker_proc = _start_subprocess("worker", [sys.executable, str(MEDLOG_MAIN), "--run_worker_only"])

    base_url = get_medlogserver_base_url()
    timeout_sec = 60
    deadline = time.monotonic() + timeout_sec
    last_log = time.monotonic()

    logger.info("Waiting for server at %s ...", base_url)
    while True:
        now = time.monotonic()

        # Detect early crash — show exit code immediately instead of timing out
        if server_proc.poll() is not None:
            worker_proc.terminate()
            _stop_oidc_mock()
            pytest.exit(
                f"Server process exited unexpectedly with code {server_proc.returncode} "
                f"(see [server] log lines above for the traceback).",
                returncode=3,
            )

        if now > deadline:
            server_proc.terminate()
            worker_proc.terminate()
            _stop_oidc_mock()
            pytest.exit(
                f"Server did not respond within {timeout_sec}s — aborting. "
                f"Check [server] log lines above for startup errors.",
                returncode=3,
            )

        if now - last_log >= 10:
            elapsed = int(now - (deadline - timeout_sec))
            logger.info("  still waiting for HTTP... (%ds elapsed)", elapsed)
            last_log = now

        try:
            r = requests.get(f"{base_url}/health")
            r.raise_for_status()
            break
        except (
            requests.HTTPError,
            requests.ConnectionError,
            urllib3.exceptions.MaxRetryError,
        ):
            time.sleep(1)

    logger.info("Server is up — waiting for initialization (drug import, search index)...")

    access_token = authorize_for_access_token(
        username=ADMIN_USER_NAME,
        pw=ADMIN_USER_PW,
        set_as_global_default_login=False,
    )

    last_log = time.monotonic()
    while True:
        now = time.monotonic()
        if now > deadline:
            server_proc.terminate()
            worker_proc.terminate()
            _stop_oidc_mock()
            pytest.exit(
                f"Server did not finish initializing within {timeout_sec}s — aborting.",
                returncode=3,
            )
        if now - last_log >= 10:
            elapsed = int(now - (deadline - timeout_sec))
            logger.info("  still initializing... (%ds elapsed)", elapsed)
            last_log = now
        r = req("api/health/report", access_token=access_token)
        if r["db_working"] and r["drugs_imported"] and r["drug_search_index_working"]:
            break
        time.sleep(2)

    logger.info("Server ready — starting test run.")

    authorize_for_access_token(
        username=ADMIN_USER_NAME,
        pw=ADMIN_USER_PW,
        set_as_global_default_login=True,
    )

    stop_event = threading.Event()

    def _monitor():
        while not stop_event.is_set():
            if server_proc.poll() is not None:
                logger.error("Server process died unexpectedly (exit code %s)", server_proc.returncode)
                os._exit(1)
            if worker_proc.poll() is not None:
                logger.error("Worker process died unexpectedly (exit code %s)", worker_proc.returncode)
                os._exit(1)
            time.sleep(1)

    monitor_thread = threading.Thread(target=_monitor, daemon=True)
    monitor_thread.start()

    yield

    stop_event.set()
    monitor_thread.join()
    server_proc.terminate()
    worker_proc.terminate()
    server_proc.wait(timeout=5)
    worker_proc.wait(timeout=5)
    _stop_oidc_mock()
    logger.info("Test session complete — server shut down.")
