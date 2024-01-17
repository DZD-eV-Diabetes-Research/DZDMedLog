from typing import Callable
import logging
import os
import getversion
import yaml

log = logging.getLogger(__name__)

if __name__ == "__main__":
    from pathlib import Path
    import sys, os

    MODULE_DIR = Path(__file__).parent.parent.absolute()
    sys.path.insert(0, os.path.normpath(MODULE_DIR))


def start():
    import medlogserver
    from medlogserver.config import Config

    config = Config()
    log.setLevel(os.getenv("LOG_LEVEL", config.LOG_LEVEL))

    # if the uvicorn log level is not defined, it will be the same as the python log level
    UVICORN_LOG_LEVEL = (
        config.UVICORN_LOG_LEVEL
        if config.UVICORN_LOG_LEVEL is not None
        else config.LOG_LEVEL
    )
    # uvicorn has a different log level system than python, we need to translate the log level setting
    UVICORN_LOG_LEVEL_map = {
        (logging.NOTSET, "NOTSET", "notset", "0"): "trace",
        (logging.CRITICAL, "50", "CRITICAL", "critical"): "critical",
        (logging.ERROR, "40", "ERROR"): "error",
        (logging.WARNING, "30", "WARNING"): "warning",
        (logging.INFO, "20", "INFO"): "info",
        (logging.DEBUG, "10", "DEBUG"): "debug",
    }

    for key, val in UVICORN_LOG_LEVEL_map.items():
        if UVICORN_LOG_LEVEL in key:
            UVICORN_LOG_LEVEL = val
            break

    print(
        f"Start medlogserver version: {getversion.get_module_version(medlogserver)[0]}"
    )
    print(f"LOG_LEVEL: {config.LOG_LEVEL}")
    print(f"UVICORN_LOG_LEVEL: {config.LOG_LEVEL}")

    log.debug(yaml.dump(config.model_dump(), sort_keys=False))
    import uvicorn

    from medlogserver.api.auth import app

    uvicorn.run(
        app,
        host=config.LISTENING_HOST,
        log_level=UVICORN_LOG_LEVEL,
        port=config.LISTENING_PORT,
    )


if __name__ == "__main__":
    start()
