import multiprocessing
import requests
import time
import urllib3
import os
import traceback

if __name__ == "__main__":
    from pathlib import Path
    import sys, os

    MODULE_DIR = Path(__file__).parent
    MODULE_PARENT_DIR = MODULE_DIR.parent.absolute()
    sys.path.insert(0, os.path.normpath(MODULE_PARENT_DIR))

from statics import (
    DB_PATH,
    DOT_ENV_FILE_PATH,
    ADMIN_USER_EMAIL,
    ADMIN_USER_PW,
    ADMIN_USER_NAME,
)


def set_config_for_test_env():
    os.environ["MEDLOG_DOT_ENV_FILE"] = DOT_ENV_FILE_PATH
    print(f"set SQL_DATABASE_URL to {DB_PATH}")
    os.environ["SQL_DATABASE_URL"] = f"sqlite+aiosqlite:///{DB_PATH}"
    os.environ["ADMIN_USER_NAME"] = ADMIN_USER_NAME
    os.environ["ADMIN_USER_PW"] = ADMIN_USER_PW
    os.environ["ADMIN_USER_EMAIL"] = ADMIN_USER_EMAIL


set_config_for_test_env()


from utils import get_medlogserver_base_url, get_dot_env_file_variable, authorize


RESET_DB = os.getenv(
    "MEDLOG_TESTS_RESET_DB",
    get_dot_env_file_variable(DOT_ENV_FILE_PATH, "MEDLOG_TESTS_RESET_DB"),
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
    Path(DB_PATH).unlink(missing_ok=True)


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


def wait_for_medlogserver_up_and_healthy(timeout_sec=120):
    medlogserver_not_available = True
    while medlogserver_not_available:
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
    print(f"SERVER UP FOR TESTING: {r.status_code}: {r.json()}")


def shutdown_medlogserver_and_backgroundworker():
    print("SHUTDOWN SERVER!")
    medlogserver_process.terminate()
    background_worker_process.terminate()
    time.sleep(5)
    print("KILL SERVER")

    # YOU ARE HERE! THIS DOES NOT KILL THE BACKGORUND WORKER PROCESS
    medlogserver_process.kill()
    medlogserver_process.join()
    medlogserver_process.close()
    background_worker_process.kill()
    background_worker_process.join()
    background_worker_process.close()


def start_medlogserver_and_backgroundworker():
    set_config_for_test_env()
    print("START medlogserver")
    medlogserver_process.start()
    wait_for_medlogserver_up_and_healthy()
    print("START medlogserver BACKGROUND WORKER")
    background_worker_process.start()
    print("STARTED medlogserver!")


start_medlogserver_and_backgroundworker()

# RUN TESTS
from tests_users import run_all_tests_users
from tests_export import test_do_export
from tests_drugv2 import test_do_drugv2
from tests_health import test_do_health
from tests_last_interview_intakes import last_interview_intakes

try:
    authorize(user=ADMIN_USER_NAME, pw=ADMIN_USER_PW)
    last_interview_intakes()
    # test_do_health()
    # run_all_tests_users()
    # test_do_drugv2()
    # test_do_export()
except Exception as e:
    print("Error in user tests")
    print(print(traceback.format_exc()))
    shutdown_medlogserver_and_backgroundworker()
    print("TESTS FAILED")
    exit(1)


shutdown_medlogserver_and_backgroundworker()
print("TESTS SUCCEDED")
exit(0)
