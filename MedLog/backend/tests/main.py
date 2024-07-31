import multiprocessing
import requests
import time
import urllib3
import os

if __name__ == "__main__":
    from pathlib import Path
    import sys, os

    MODULE_DIR = Path(__file__).parent
    MODULE_PARENT_DIR = MODULE_DIR.parent.absolute()
    sys.path.insert(0, os.path.normpath(MODULE_PARENT_DIR))

DB_PATH = f"{Path(__file__).parent}/testdb.sqlite"
DOT_ENV_FILE_PATH = f"{Path(__file__).parent}/.env"
ADMIN_USER_NAME = "admin"
ADMIN_USER_PW = "password123"
ADMIN_USER_EMAIL = "user@test.de"
RESET_DB = os.getenv("MEDLOG_TESTS_RESET_DB", "False").lower() in (
    "true",
    "1",
    "t",
    "y",
    "yes",
)

if RESET_DB:
    Path(DB_PATH).unlink(missing_ok=True)


def set_config_for_test_env():
    os.environ["MEDLOG_DOT_ENV_FILE"] = DOT_ENV_FILE_PATH
    print(f"set SQL_DATABASE_URL to {DB_PATH}")
    os.environ["SQL_DATABASE_URL"] = f"sqlite+aiosqlite:///{DB_PATH}"
    os.environ["ADMIN_USER_NAME"] = ADMIN_USER_NAME
    os.environ["ADMIN_USER_PW"] = ADMIN_USER_PW
    os.environ["ADMIN_USER_EMAIL"] = ADMIN_USER_EMAIL


set_config_for_test_env()

from medlogserver.main import start as medlogserver_start
from medlogserver.worker.worker import run_background_worker

from utils import get_medlogserver_base_url


medlogserver_process = multiprocessing.Process(
    target=medlogserver_start,
    name="DZDMedLogServer",
    kwargs={"with_background_worker": False},
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
from MedLog.backend.tests.tests_users import run_tests

try:
    run_tests()
except:
    shutdown_medlogserver_and_backgroundworker()
    print("TESTS FAILED")
    exit(1)


shutdown_medlogserver_and_backgroundworker()
print("TESTS SUCCEDED")
exit(0)
