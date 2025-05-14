import logging
import sys, os

from medlogserver.config import Config

config = Config()
from fastapi.logger import logger

APP_LOGGER_DEFAULT_NAME = "MedLog"


# suppress "AttributeError: module 'bcrypt' has no attribute '__about__'"-warning
# https://github.com/pyca/bcrypt/issues/684
logging.getLogger("passlib").setLevel(logging.ERROR)


def get_loglevel():
    return os.getenv("LOG_LEVEL", config.LOG_LEVEL)


log = None


def get_logger(name: str = APP_LOGGER_DEFAULT_NAME, prefix: str = "") -> logging.Logger:
    global log
    if log is None or log.name != name:
        log = logging.getLogger(name)
        log.setLevel(get_loglevel())

        # Clear existing handlers to avoid duplicate logs
        log.handlers.clear()

        handler = logging.StreamHandler(sys.stdout)

        format_string = f"{prefix}%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(format_string)
        handler.setFormatter(formatter)

        log.addHandler(handler)

    return log


def get_uvicorn_loglevel():
    # uvicorn has a different log level naming system than python, we need to translate the log level setting
    UVICORN_LOG_LEVEL_map = {
        (logging.NOTSET, "NOTSET", "notset", "0"): "trace",
        (logging.CRITICAL, "50", "CRITICAL", "critical", "FATAL", "fatal"): "critical",
        (logging.ERROR, "40", "ERROR", "error"): "error",
        (logging.WARNING, "30", "WARNING", "warning", "WARN", "warn"): "warning",
        (logging.INFO, "20", "INFO", "info"): "info",
        (logging.DEBUG, "10", "DEBUG", "debug"): "debug",
    }

    # if the uvicorn log level is not defined, it will be the same as the python log level
    UVICORN_LOG_LEVEL = (
        config.SERVER_UVICORN_LOG_LEVEL
        if config.SERVER_UVICORN_LOG_LEVEL is not None
        else config.LOG_LEVEL
    )
    for key, val in UVICORN_LOG_LEVEL_map.items():
        if UVICORN_LOG_LEVEL in key:
            UVICORN_LOG_LEVEL = val
            break
    return UVICORN_LOG_LEVEL
