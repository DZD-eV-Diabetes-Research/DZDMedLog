from medlogserver.app import app

from medlogserver.config import Config

config = Config()

from medlogserver.log import get_logger

log = get_logger()
