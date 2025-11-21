import logging
import sys
import os
from typing import Optional

from medlogserver.config import Config

config = Config()


APP_LOGGER_DEFAULT_NAME = config.APP_NAME


# suppress "AttributeError: module 'bcrypt' has no attribute '__about__'"-warning
# https://github.com/pyca/bcrypt/issues/684
logging.getLogger("passlib").setLevel(logging.ERROR)


# ANSI Color codes
class Colors:
    """ANSI color codes for terminal output"""

    RESET = "\033[0m"

    # Log level colors
    DEBUG = "\033[36m"  # Cyan
    INFO = "\033[32m"  # Green
    WARNING = "\033[33m"  # Yellow
    ERROR = "\033[31m"  # Red
    CRITICAL = "\033[35m"  # Magenta

    # Module name colors - neutral, calming palette
    MODULE_COLORS = [
        "\033[34m",  # Blue
        "\033[36m",  # Cyan
        "\033[32m",  # Green
        "\033[35m",  # Magenta
        "\033[37m",  # White
        "\033[94m",  # Bright Blue
        "\033[96m",  # Bright Cyan
        "\033[92m",  # Bright Green
        "\033[95m",  # Bright Magenta
    ]


def get_loglevel():
    return os.getenv("LOG_LEVEL", config.LOG_LEVEL)


active_loggers_store = None


def get_logger(
    name: Optional[str] = APP_LOGGER_DEFAULT_NAME, modulename: Optional[str] = ""
) -> logging.Logger:
    global active_loggers_store
    if active_loggers_store is None:
        active_loggers_store = {}

    store_name = f"{name}{modulename}"
    module = ""
    if modulename:
        module = f" - [{modulename}]"
    logger_ = None

    if store_name not in active_loggers_store:
        logger_ = logging.getLogger(store_name)
        logger_.setLevel(get_loglevel())

        # Clear existing handlers to avoid duplicate logs
        logger_.handlers.clear()

        handler = logging.StreamHandler(sys.stdout)

        format_string = f"%(asctime)s - {name}{module} - %(levelname)s - %(message)s"
        formatter = logging.Formatter(format_string)
        handler.setFormatter(formatter)

        logger_.addHandler(handler)
        active_loggers_store[store_name] = logger_
    else:
        logger_ = active_loggers_store[store_name]

    return logger_


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
