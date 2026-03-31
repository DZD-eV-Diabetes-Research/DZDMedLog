import logging
import logging.handlers
import sys
import os
import hashlib
import multiprocessing
from typing import Optional, Dict, Tuple
import inspect
from pathlib import Path
from medlogserver.config import Config

config = Config()

APP_LOGGER_DEFAULT_NAME = config.APP_NAME

logging.getLogger("passlib").setLevel(logging.ERROR)


class Colors:
    RESET = "\033[0m"
    DEBUG = "\033[36m"
    INFO = "\033[32m"
    WARNING = "\033[33m"
    ERROR = "\033[31m"
    CRITICAL = "\033[35m"
    MODULE_COLORS = [
        "\033[34m",
        "\033[33m",
        "\033[32m",
        "\033[36m",
        "\033[35m",
        "\033[94m",
        "\033[93m",
        "\033[92m",
        "\033[96m",
        "\033[95m",
        "\033[91m",
    ]


def get_loglevel():
    return os.getenv("LOG_LEVEL", config.LOG_LEVEL)


def get_module_color(module_name: str) -> str:
    if config.LOG_DISABLE_COLORS:
        return ""
    hash_digest = hashlib.md5(module_name.encode()).hexdigest()
    color_index = int(hash_digest, 16) % len(Colors.MODULE_COLORS)
    return Colors.MODULE_COLORS[color_index]


def get_loglevel_color(level: int) -> str:
    if config.LOG_DISABLE_COLORS:
        return ""
    if level >= logging.CRITICAL:
        return Colors.CRITICAL
    elif level >= logging.ERROR:
        return Colors.ERROR
    elif level >= logging.WARNING:
        return Colors.WARNING
    elif level >= logging.INFO:
        return Colors.INFO
    return Colors.DEBUG


class ColoredFormatter(logging.Formatter):
    GRAY = "\033[90m"

    def format(self, record):
        levelcolor = get_loglevel_color(record.levelno)
        record.levelname = f"{levelcolor}{record.levelname}{Colors.RESET if not config.LOG_DISABLE_COLORS else ''}"
        result = super().format(record)
        if not config.LOG_DISABLE_COLORS:
            parts = result.split(" - ", 1)
            if parts:
                result = f"{self.GRAY}{parts[0]}{Colors.RESET} - {parts[1]}"
        return result


# --- Multiprocessing-safe logging infrastructure ---
# A single Queue is created at module import time in the main process.
# Worker processes detect they are not the main process and install a
# QueueHandler on the root logger, forwarding all records back here.

_log_queue: multiprocessing.Queue = multiprocessing.Queue(-1)
_listener: Optional[logging.handlers.QueueListener] = None
active_loggers_store: Dict[str, logging.Logger] = {}


def _make_handler(format_string: str) -> logging.StreamHandler:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(ColoredFormatter(format_string))
    return h


def _ensure_listener_running(handler: logging.Handler):
    """Start the QueueListener in the main process if not already running."""
    global _listener
    if _listener is None:
        _listener = logging.handlers.QueueListener(
            _log_queue, handler, respect_handler_level=True
        )
        _listener.start()
        import atexit

        atexit.register(_listener.stop)


def _is_worker_process() -> bool:
    return multiprocessing.current_process().name != "MainProcess"


def _ensure_worker_configured():
    """
    In a worker process, redirect the root logger to the shared queue.
    Called lazily on first get_logger() call inside the worker.
    """
    root = logging.getLogger()
    if any(isinstance(h, logging.handlers.QueueHandler) for h in root.handlers):
        return  # already configured
    root.handlers.clear()
    root.addHandler(logging.handlers.QueueHandler(_log_queue))
    root.setLevel(get_loglevel())


# --- Public API ---


def get_logger(
    name: Optional[str] = APP_LOGGER_DEFAULT_NAME, modulename: Optional[str] = ""
) -> logging.Logger:
    global active_loggers_store
    if active_loggers_store is None:
        active_loggers_store = {}
    if not modulename:
        modulename = Path(inspect.stack()[1].filename).name
    store_name = f"{name}{modulename}"
    module = ""
    module_color_code = ""

    if modulename:
        module_color_code = get_module_color(modulename)
        module = f" - [{module_color_code}{modulename}{Colors.RESET}]"

    logger_ = None

    if store_name not in active_loggers_store:
        logger_ = logging.getLogger(store_name)
        logger_.setLevel(get_loglevel())

        # Clear existing handlers to avoid duplicate logs
        logger_.handlers.clear()

        handler = logging.StreamHandler(sys.stdout)

        format_string = f"%(asctime)s - {name}{module} - %(levelname)s - %(message)s"
        formatter = ColoredFormatter(format_string)
        handler.setFormatter(formatter)

        logger_.addHandler(handler)
        active_loggers_store[store_name] = logger_
    else:
        logger_ = active_loggers_store[store_name]

    return logger_


def get_uvicorn_loglevel() -> str:
    UVICORN_LOG_LEVEL_map: Dict[Tuple[int | str, ...], str] = {
        (logging.NOTSET, "NOTSET", "notset", "0"): "trace",
        (logging.CRITICAL, "50", "CRITICAL", "critical", "FATAL", "fatal"): "critical",
        (logging.ERROR, "40", "ERROR", "error"): "error",
        (logging.WARNING, "30", "WARNING", "warning", "WARN", "warn"): "warning",
        (logging.INFO, "20", "INFO", "info"): "info",
        (logging.DEBUG, "10", "DEBUG", "debug"): "debug",
    }
    UVICORN_LOG_LEVEL: str = (
        config.SERVER_UVICORN_LOG_LEVEL
        if config.SERVER_UVICORN_LOG_LEVEL is not None
        else config.LOG_LEVEL
    )
    for key, val in UVICORN_LOG_LEVEL_map.items():
        if UVICORN_LOG_LEVEL in key:
            return val
    return "info"
