from sqlalchemy.ext.asyncio import create_async_engine


from medlogserver.config import Config

config = Config()

db_engine = create_async_engine(
    str(config.SQL_DATABASE_URL), echo=config.DEBUG_SQL, future=True
)
