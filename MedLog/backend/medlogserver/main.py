from typing import Dict
import logging
import os
import getversion
import yaml
import sys

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
    from medlogserver.log import get_logger, get_uvicorn_loglevel

    config = Config()
    log = get_logger(__name__)
    print(log.handlers)

    print(
        f"Start medlogserver version: {getversion.get_module_version(medlogserver)[0]}"
    )
    print(f"LOG_LEVEL: {config.LOG_LEVEL}")
    print(f"UVICORN_LOG_LEVEL: {config.LOG_LEVEL}")
    log.debug("----CONFIG-----")
    log.debug(yaml.dump(config.model_dump(), sort_keys=False))
    log.debug("----CONFIG-END-----")
    import uvicorn
    from uvicorn.config import LOGGING_CONFIG
    from medlogserver.api.auth import app

    uvicorn_log_config: Dict = LOGGING_CONFIG

    uvicorn.run(
        app,
        host=config.LISTENING_HOST,
        log_level=get_uvicorn_loglevel(),
        port=config.LISTENING_PORT,
        log_config=uvicorn_log_config,
    )


if __name__ == "__main__":
    start()
