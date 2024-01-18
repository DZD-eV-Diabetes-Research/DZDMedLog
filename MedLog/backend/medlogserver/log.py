import logging
import sys, os

from medlogserver.config import Config

config = Config()


def get_logger(name: str) -> logging.Logger:
    level = os.getenv("LOG_LEVEL", config.LOG_LEVEL)
    log = logging.getLogger(name)
    # handler = logging.StreamHandler(sys.stdout)
    # if handler not in log.handlers:
    #    log.addHandler(handler)
    log.setLevel(level)
    for handler in log.handlers:
        handler.setLevel(level)
    print("log.handlers", log.handlers)

    return log


def get_uvicorn_loglevel():
    # uvicorn has a different log level system than python, we need to translate the log level setting
    UVICORN_LOG_LEVEL_map = {
        (logging.NOTSET, "NOTSET", "notset", "0"): "trace",
        (logging.CRITICAL, "50", "CRITICAL", "critical"): "critical",
        (logging.ERROR, "40", "ERROR", "error"): "error",
        (logging.WARNING, "30", "WARNING", "warning"): "warning",
        (logging.INFO, "20", "INFO", "info"): "info",
        (logging.DEBUG, "10", "DEBUG", "debug"): "debug",
    }
    # if the uvicorn log level is not defined, it will be the same as the python log level
    UVICORN_LOG_LEVEL = (
        config.UVICORN_LOG_LEVEL
        if config.UVICORN_LOG_LEVEL is not None
        else config.LOG_LEVEL
    )
    for key, val in UVICORN_LOG_LEVEL_map.items():
        if UVICORN_LOG_LEVEL in key:
            UVICORN_LOG_LEVEL = val
            break
    return UVICORN_LOG_LEVEL
