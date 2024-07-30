import multiprocessing
import requests
import time

if __name__ == "__main__":
    from pathlib import Path
    import sys, os

    MODULE_DIR = Path(__file__).parent
    MODULE_PARENT_DIR = MODULE_DIR.parent.absolute()
    sys.path.insert(0, os.path.normpath(MODULE_PARENT_DIR))


from medlogserver.main import start as medlogserver_start
from medlogserver.config import Config


medlogserver_config = Config()


medlogserver_process = multiprocessing.Process(
    target=medlogserver_start, name="DZDMedLogBackgroundWorker"
)
medlogserver_base_url = f"http://{medlogserver_config.SERVER_HOSTNAME}:{medlogserver_config.SERVER_LISTENING_PORT}"


def wait_for_medlogserver_up_and_healthy(timeout_sec=120):
    medlogserver_not_available = True
    while medlogserver_not_available:
        try:
            r = requests.get(f"{medlogserver_base_url}/health")
            r.raise_for_status()
            medlogserver_not_available = False
        except requests.HTTPError:
            time.sleep(1)
        print(f"SERVER UP FOR TESTING: {r.status_code}: {r.json()}")


# wait_for_medlogserver_up_and_healthy()
medlogserver_process.terminate()
medlogserver_process.join()
