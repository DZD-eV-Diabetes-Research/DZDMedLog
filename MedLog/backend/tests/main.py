from typing import List
import multiprocessing
import requests
import time
import urllib3
import os
import traceback
import types
from pathlib import Path
import sys, os
import threading
import json

if __name__ == "__main__":
    MODULE_DIR = Path(__file__).parent
    MODULE_PARENT_DIR = MODULE_DIR.parent.absolute()
    sys.path.insert(0, os.path.normpath(MODULE_PARENT_DIR))

from statics import (
    DB_PATH,
    DOT_ENV_FILE_PATH,
    ADMIN_USER_EMAIL,
    ADMIN_USER_PW,
    ADMIN_USER_NAME,
    DRUG_IMPORTER_ALLOW_MANUAL_UPDATE_DRUG_DB,
    SYSTEM_ANNOUNCEMENTS,
)


def set_config_for_test_env():
    os.environ["MEDLOG_DOT_ENV_FILE"] = DOT_ENV_FILE_PATH

    SQL_DATABASE_URL = os.getenv("SQL_DATABASE_URL", default=None)

    os.environ["SQL_DATABASE_URL"] = (
        SQL_DATABASE_URL
        if SQL_DATABASE_URL is not None
        else f"sqlite+aiosqlite:///{DB_PATH}"
    )
    print(f"set SQL_DATABASE_URL to {os.environ['SQL_DATABASE_URL']}")
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


set_config_for_test_env()


from utils import (
    get_medlogserver_base_url,
    get_dot_env_file_variable,
    authorize,
    get_test_functions_from_file_or_module,
)


RESET_DB = os.getenv(
    "MEDLOG_TESTS_RESET_DB",
    get_dot_env_file_variable(
        DOT_ENV_FILE_PATH, "MEDLOG_TESTS_RESET_DB", default="True"
    ),
).lower() in (
    "true",
    "1",
    "t",
    "y",
    "yes",
)

if RESET_DB:
    print(
        f"!!RESET DB AT {DB_PATH}. If you want to have a persisting test db, change the value for env var `MEDLOG_TESTS_RESET_DB` to false or remove it."
    )
    SQL_DATABASE_URL: str = os.getenv("SQL_DATABASE_URL", default=None)
    if SQL_DATABASE_URL.startswith("sqlite"):
        Path(DB_PATH).unlink(missing_ok=True)
    else:
        print(
            "WARNING: RESET_DB is enabled but SQL_DATABASE_URL is set to an external database. Can not reset the DB. This must be done externaly."
        )
if __name__ == "__main__":
    multiprocessing.set_start_method("fork")  # explicit, works on Linux/Mac

    from medlogserver.main import start as medlogserver_start
    from medlogserver.worker.worker import run_background_worker

    medlogserver_process = multiprocessing.Process(
        target=medlogserver_start,
        name="DZDMedLogServer",
        kwargs={},
    )

    background_worker_process = multiprocessing.Process(
        target=run_background_worker,
        name="DZDMedLogBackgroundWorker",
        kwargs={"run_in_extra_process": False},
    )


medlogserver_base_url = get_medlogserver_base_url()


def wait_for_medlogserver_up_and_healthy(timeout_sec=20):
    from utils import req, dict_must_contain
    import time

    deadline = time.monotonic() + timeout_sec

    # --- Wait for server to respond ---
    medlogserver_not_available = True
    while medlogserver_not_available:
        if time.monotonic() > deadline:
            shutdown_medlogserver_and_backgroundworker()
            raise TimeoutError(f"Server did not come up within {timeout_sec}s")
        try:
            r = requests.get(f"{medlogserver_base_url}/health")
            r.raise_for_status()
            medlogserver_not_available = False
        except (
            requests.HTTPError,
            requests.ConnectionError,
            urllib3.exceptions.MaxRetryError,
        ):
            time.sleep(1)

    print(f"SERVER UP FOR LISTENING: {r.status_code}")

    # --- Wait for server to finish initializing ---
    access_token = authorize(
        username=ADMIN_USER_NAME,
        pw=ADMIN_USER_PW,
        set_as_global_default_login=False,
    )
    medlogserver_not_initialized = True
    while medlogserver_not_initialized:
        if time.monotonic() > deadline:
            raise TimeoutError(
                f"Server did not finish initializing within {timeout_sec}s"
            )
        from medlogserver.api.routes.routes_healthcheck import HealthCheckReport

        r = req("api/health/report", access_token=access_token)
        print("health res", r)
        print("health medlogserver_process.exitcode", medlogserver_process.exitcode)
        print(
            "health background_worker_process.exitcode",
            background_worker_process.exitcode,
        )

        if r["db_working"] and r["drugs_imported"] and r["drug_search_index_working"]:
            medlogserver_not_initialized = False

        time.sleep(2)

    print(f"SERVER READY FOR TESTING: {r}")


def shutdown_medlogserver_and_backgroundworker():
    print("SHUTDOWN SERVER!")
    medlogserver_process.terminate()
    background_worker_process.terminate()
    medlogserver_process.join(timeout=5)
    background_worker_process.join(timeout=5)
    print("KILL SERVER")


def start_medlogserver_and_backgroundworker():
    set_config_for_test_env()
    print("START medlogserver")
    medlogserver_process.start()
    print("START medlogserver BACKGROUND WORKER")
    background_worker_process.start()
    wait_for_medlogserver_up_and_healthy()
    print("STARTED medlogserver!")


def monitor_medlogserver_and_backgroundworker(monitor_stop_event: threading.Event):
    try:
        while not monitor_stop_event.is_set():
            if not medlogserver_process.is_alive():
                print("❌ medlogserver_process died")
                shutdown_medlogserver_and_backgroundworker()
                os._exit(1)

            if not background_worker_process.is_alive():
                print("❌ background_worker_process died")
                shutdown_medlogserver_and_backgroundworker()
                os._exit(1)

            time.sleep(1)
    except KeyboardInterrupt:
        shutdown_medlogserver_and_backgroundworker()
        monitor_stop_event.set()
        exit(0)


start_medlogserver_and_backgroundworker()
monitor_stop_event = threading.Event()
monitor_thread = threading.Thread(
    target=monitor_medlogserver_and_backgroundworker,
    args=(monitor_stop_event,),
    daemon=True,
)
monitor_thread.start()
successfull_test_files: List[str] = []


def run_single_test_file(
    file_name_or_module: str | types.ModuleType,
    authorize_before: bool = False,
    exit_on_success: bool = False,
    exit_on_fail: bool = True,
):
    all_function_success = True
    module_human_identifier = str(file_name_or_module)
    if isinstance(file_name_or_module, types.ModuleType):
        module_human_identifier = str(file_name_or_module.__file__)

    print("file_name_or_module", file_name_or_module)
    try:
        if authorize_before:
            authorize(
                username=ADMIN_USER_NAME,
                pw=ADMIN_USER_PW,
                set_as_global_default_login=True,
            )
        tests_successfull: List[str] = []
        for name, test_function in get_test_functions_from_file_or_module(
            file_name_or_module
        ):
            print(f"--------------- RUN test function {name}")
            test_function()
            tests_successfull.append(name)
    except Exception as e:
        all_function_success = False
        print("Error in tests")
        print(print(traceback.format_exc()))
        shutdown_medlogserver_and_backgroundworker()
        print(f"🚫 TEST MODULE '{module_human_identifier}' FAILED")
        print(f"\t🚫 TEST '{test_function.__name__}' FAILED")
        if exit_on_fail:
            exit(1)
    successfull_test_files.append(module_human_identifier)
    if exit_on_success:
        shutdown_medlogserver_and_backgroundworker()
        print("✅️ TESTS SUCCEDED")
        exit(0)


if __name__ == "__main__":
    import os
    import importlib

    authorize(
        username=ADMIN_USER_NAME, pw=ADMIN_USER_PW, set_as_global_default_login=True
    )
    # RUN ALL TEST SCRIPTS
    if 1 == 1:
        # find all files named tests_*.py in current directory
        for filename in os.listdir(os.path.dirname(__file__)):
            if filename.startswith("tests_") and filename.endswith(".py"):
                module_name = filename[:-3]  # strip .py
                module = importlib.import_module(module_name)
                run_single_test_file(module)

    # RUN SPECIFIC TEST SCRIPTS
    if 1 == 0:
        import tests_config
        import tests_health
        import tests_event
        import tests_users
        import tests_export
        import tests_study
        import tests_study_permission
        import tests_interview
        import tests_drug
        import tests_intake
        import tests_drug_db_updater
        import tests_last_interview_intakes

        run_single_test_file(tests_config)
        run_single_test_file(tests_health)
        run_single_test_file(tests_users)
        run_single_test_file(tests_study)
        run_single_test_file(tests_event)
        run_single_test_file(tests_interview)
        run_single_test_file(tests_intake)
        run_single_test_file(tests_last_interview_intakes)
        run_single_test_file(tests_study_permission)
        run_single_test_file(tests_export)
        run_single_test_file(tests_drug)
        run_single_test_file(tests_drug_db_updater)
    monitor_stop_event.set()
    monitor_thread.join()
    shutdown_medlogserver_and_backgroundworker()

    for test_file in successfull_test_files:
        print(f"\t✅️ {test_file}")
    print("✅️ TESTS SUCCEDED")

    exit(0)
