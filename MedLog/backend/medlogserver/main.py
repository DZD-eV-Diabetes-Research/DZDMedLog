from typing import Dict, List
import logging
import os
import getversion
import yaml
import sys
import asyncio
import json
import argparse

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
    from pathlib import Path
    import sys, os

    MODULE_DIR = Path(__file__).parent
    MODULE_PARENT_DIR = MODULE_DIR.parent.absolute()
    sys.path.insert(0, os.path.normpath(MODULE_PARENT_DIR))

# Import and load config
from medlogserver.config import Config

config = Config()


def start(with_background_worker: bool = True):
    import medlogserver

    from medlogserver.log import (
        get_logger,
        get_loglevel,
        get_uvicorn_loglevel,
        APP_LOGGER_DEFAULT_NAME,
    )

    log = get_logger()

    print(
        f"Start medlogserver version: {getversion.get_module_version(medlogserver)[0]}"
    )

    log.debug("----CONFIG-----")
    log.debug(yaml.dump(json.loads(config.model_dump_json()), sort_keys=False))
    log.debug("----CONFIG-END-----")
    # test_exporter()
    # exit()
    print(f"LOG_LEVEL: {config.LOG_LEVEL}")
    print(f"UVICORN_LOG_LEVEL: {get_uvicorn_loglevel()}")
    print(
        f"allow_origins=[{config.CLIENT_URL}, {str(config.get_server_url()).rstrip('/')}]"
    )

    from medlogserver.db._init_db import init_db
    import uvicorn
    from uvicorn.config import LOGGING_CONFIG
    from medlogserver.app import app, add_api_middleware
    from medlogserver.api.routers_map import mount_fast_api_routers
    from medlogserver.worker.worker import run_background_worker

    mount_fast_api_routers(app)
    add_api_middleware(app)
    uvicorn_log_config: Dict = LOGGING_CONFIG
    uvicorn_log_config["loggers"][APP_LOGGER_DEFAULT_NAME] = {
        "handlers": ["default"],
        "level": get_loglevel(),
    }
    event_loop = asyncio.get_event_loop()
    uvicorn_config = uvicorn.Config(
        app=app,
        host=config.SERVER_LISTENING_HOST,
        port=config.SERVER_LISTENING_PORT,
        log_level=get_uvicorn_loglevel(),
        log_config=uvicorn_log_config,
        loop=event_loop,
    )
    uvicorn_server = uvicorn.Server(config=uvicorn_config)

    event_loop.run_until_complete(init_db())
    if with_background_worker:
        # Start background worker in second process
        run_background_worker(run_in_extra_process=True)
    event_loop.run_until_complete(uvicorn_server.serve())


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
        start(with_background_worker=config.BACKGROUND_WORKER_START_IN_EXTRA_PROCESS)
