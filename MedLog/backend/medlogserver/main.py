from typing import Dict, List, Optional
import logging
import os
import getversion
import yaml
import sys
import asyncio
import json
import argparse
from fastapi import FastAPI
from pathlib import Path
import sys, os
from contextlib import asynccontextmanager
import time

# Main can be started with arguments. Lets parse these first.


arg_parser = argparse.ArgumentParser("DZDMedLog")
arg_parser.add_argument(
    "--set_version_file",
    help="Set this flag to just write the __version__.py file based on the git version. Only needed for CI/CD pipeline.",
    action="store_true",
)
arg_parser.add_argument(
    "--run_worker_only",
    help="Set this flag to just run the background worker without the unvicorn webserver.",
    action="store_true",
)

# Setup logging
log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler(sys.stdout))


# Add MedLogServer to global Python modules.
# This way we address medlogserver as a module for imports without installing it first.
# e.g. "from medlogserver import config"
if __name__ == "__main__":

    MODULE_DIR = Path(__file__).parent
    MODULE_PARENT_DIR = MODULE_DIR.parent.absolute()
    sys.path.insert(0, os.path.normpath(MODULE_PARENT_DIR))

# Import and load config
from medlogserver.config import Config

# memory profiling- uncomment for activating
"""
print(
   "WARNING by Tim: Memory Profiler is still enabled. This degrades perfomance drasticly. Please remove for production!!!!"
)
from memory_profiler import profile
@profile
"""


def start():
    import medlogserver

    print(
        f"Start medlogserver version: {getversion.get_module_version(medlogserver)[0]} under user with id {os.getuid()}"
    )
    from medlogserver.log import (
        get_logger,
        get_loglevel,
        get_uvicorn_loglevel,
        APP_LOGGER_DEFAULT_NAME,
    )

    log = get_logger()
    log.info("Parse config for completeness...")
    config = Config()
    log.debug("----CONFIG-----")
    log.debug(yaml.dump(json.loads(config.model_dump_json()), sort_keys=False))
    log.debug("----CONFIG-END-----")
    log.info("...config ok!")
    # test_exporter()
    # exit()
    print(f"LOG_LEVEL: {config.LOG_LEVEL}")
    print(f"UVICORN_LOG_LEVEL: {get_uvicorn_loglevel()}")

    from medlogserver.db._init_db import init_db
    import uvicorn
    from uvicorn.config import LOGGING_CONFIG
    from medlogserver.app import FastApiAppContainer

    from medlogserver.worker.worker import run_background_worker

    if config.CLIENT_URL == config.get_server_url():
        if (
            not Path(config.FRONTEND_FILES_DIR).exists()
            or not Path(config.FRONTEND_FILES_DIR, "index.html").exists()
        ):
            raise ValueError(
                "Can not find frontend files. Maybe you need to build the frontend first. Try to run 'make frontend'"
            )

    uvicorn_log_config: Dict = LOGGING_CONFIG
    uvicorn_log_config["loggers"][APP_LOGGER_DEFAULT_NAME] = {
        "handlers": ["default"],
        "level": get_loglevel(),
    }
    fast_api_app_container = FastApiAppContainer()
    event_loop = asyncio.get_event_loop()
    uvicorn_config = uvicorn.Config(
        app=fast_api_app_container.app,
        host=config.SERVER_LISTENING_HOST,
        port=config.SERVER_LISTENING_PORT,
        log_level=get_uvicorn_loglevel(),
        log_config=uvicorn_log_config,
        loop=event_loop,
        lifespan="on",
    )
    uvicorn_server = uvicorn.Server(config=uvicorn_config)
    from medlogserver.db.drug_data.importers.wido_gkv_arzneimittelindex import (
        WidoAiImporter52,
    )

    event_loop.run_until_complete(init_db())

    if config.DEMO_MODE:
        log.warning(
            f"Hey, we are in demo mode. Login as admin with the following account:"
        )
        log.info(
            f"USERNAME: {config.ADMIN_USER_NAME}\nPASSWORD: {config.ADMIN_USER_PW.get_secret_value()}"
        )
    cancel_background_worker_func = lambda: log.info(
        "No background worker shutdown neccessary"
    )
    if config.BACKGROUND_WORKER_START_IN_EXTRA_PROCESS:
        # Start background worker in second process
        background_worker = run_background_worker(run_in_extra_process=True)

        def cancel_background_worker():
            log.info("Stop background worker process...")
            background_worker.terminate()
            time.sleep(3)
            if background_worker.is_alive():
                log.info("Kill background worker...")
                background_worker.kill()
            background_worker.join()

        cancel_background_worker_func = cancel_background_worker
        fast_api_app_container.add_shutdown_callback(cancel_background_worker)

    try:
        log.debug("Start uvicorn server...")
        event_loop.run_until_complete(uvicorn_server.serve())
    except (KeyboardInterrupt, Exception) as e:
        if isinstance(e, KeyboardInterrupt):
            log.info("KeyboardInterrupt shutdown...")
        if isinstance(e, Exception):
            log.info("Panic shutdown...")
        if background_worker is not None and background_worker.is_alive():
            cancel_background_worker_func()
        if isinstance(e, Exception):
            raise e


if __name__ == "__main__":
    args = arg_parser.parse_args()
    if args.set_version_file:
        print("Write `__version__.py` file...")
        from medlogserver.utils import set_version_file

        version_file = set_version_file(MODULE_DIR)
        version = version_file.read_text()
        print(f"Wrote '{version}' into '{version_file.absolute()}'")
        exit()
    if args.run_worker_only:
        print("Run only background server.")
        from medlogserver.worker.worker import run_background_worker

        run_background_worker(run_in_extra_process=False)
    else:
        start()
