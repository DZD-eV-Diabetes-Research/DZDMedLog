from sqlalchemy.ext.asyncio import create_async_engine
from medlogserver.config import Config
from medlogserver.log import get_logger

config = Config()
log = get_logger()


db_engine = create_async_engine(
    config.SQL_DATABASE_URL, echo=config.DEBUG_SQL, future=True
)
