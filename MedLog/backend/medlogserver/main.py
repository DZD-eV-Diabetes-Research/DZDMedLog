from typing import Dict
import logging
import os
import getversion
import yaml
import sys
import asyncio

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler(sys.stdout))
if __name__ == "__main__":
    from pathlib import Path
    import sys, os

    MODULE_DIR = Path(__file__).parent.parent.absolute()
    sys.path.insert(0, os.path.normpath(MODULE_DIR))


def start():
    import medlogserver
    from medlogserver.config import Config

    from medlogserver.log import (
        get_logger,
        get_loglevel,
        get_uvicorn_loglevel,
        APP_LOGGER_DEFAULT_NAME,
    )

    config = Config()
    log = get_logger()

    print(
        f"Start medlogserver version: {getversion.get_module_version(medlogserver)[0]}"
    )

    log.debug("----CONFIG-----")
    log.debug(yaml.dump(config.model_dump(), sort_keys=False))
    log.debug("----CONFIG-END-----")
    print(f"LOG_LEVEL: {config.LOG_LEVEL}")
    print(f"UVICORN_LOG_LEVEL: {get_uvicorn_loglevel()}")

    from medlogserver.db._init_db import init_db

    asyncio.run(init_db())
    import uvicorn
    from uvicorn.config import LOGGING_CONFIG
    from medlogserver.app import app, add_api_middleware
    from medlogserver.api.routers_map import mount_fast_api_routers

    mount_fast_api_routers(app)
    add_api_middleware(app)
    uvicorn_log_config: Dict = LOGGING_CONFIG
    uvicorn_log_config["loggers"][APP_LOGGER_DEFAULT_NAME] = {
        "handlers": ["default"],
        "level": get_loglevel(),
    }

    from worker.wido_gkv_arzneimittelindex_importer import load_data

    if 1 == 2:
        load_data(
            source_data_dir="/home/tim/Repos/github.com/DZD-eV-Diabetes-Research/DZDMedLog/GKV_AI_StammPlus/202301"
        )
        exit()

    uvicorn.run(
        app,
        host=config.SERVER_LISTENING_HOST,
        log_level=get_uvicorn_loglevel(),
        port=config.SERVER_LISTENING_PORT,
        log_config=uvicorn_log_config,
    )


if __name__ == "__main__":
    start()
