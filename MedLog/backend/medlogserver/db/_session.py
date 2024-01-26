from typing import AsyncGenerator, List


from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
import contextlib
from medlogserver.config import Config
from medlogserver.db._engine import db_engine

config = Config()


async def get_async_session() -> AsyncSession:
    async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


get_async_session_context = contextlib.asynccontextmanager(get_async_session)
