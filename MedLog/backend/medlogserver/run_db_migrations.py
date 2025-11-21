# self-note to tim: `alembic stamp head` to baptise "existing-before-alembic-introduction"-databases
import os

from pathlib import Path
import sqlite3
from urllib.parse import urlparse
from medlogserver.log import get_logger
import alembic.config


def run_db_migrations():
    """Temporarily change directory, then restore the original."""

    log = get_logger(modulename="DB MIGRATOR")
    log.info("Start DB Migrations")
    original_dir = os.getcwd()
    try:
        alembic_dir = Path(__file__).parent
        os.chdir(alembic_dir)
        alembicArgs = [
            "upgrade",
            "head",
        ]
        log.debug(f"Call alembic (from dir: '{alembic_dir}') with args: {alembicArgs}")
        alembic.config.main(argv=alembicArgs)

    finally:
        log.info("DB Migrations Completed!")
        os.chdir(original_dir)
